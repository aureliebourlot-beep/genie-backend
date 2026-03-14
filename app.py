from flask import Flask, request, jsonify
import os
import requests
import time

app = Flask(__name__)

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID")

headers = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
    "Content-Type": "application/json"
}

@app.route("/")
def home():
    return "GENIE BACKEND OK"

@app.route("/ask")
def ask():
    question = request.args.get("question")

    if not question:
        return jsonify({"error": "Le paramètre question est requis"}), 400

    # 1) Démarrer la conversation
    start_url = f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/start-conversation"
    start_resp = requests.post(
        start_url,
        headers=headers,
        json={"content": question}
    )
    start_resp.raise_for_status()
    start_data = start_resp.json()

    conversation_id = start_data.get("conversation_id")
    message_id = start_data.get("message_id")

    if not conversation_id or not message_id:
        return jsonify({
            "error": "conversation_id ou message_id manquant",
            "start_response": start_data
        }), 500

    # 2) Vérifier l'état du message
    status_url = f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/{conversation_id}/messages/{message_id}"

    final_data = None

    for _ in range(12):
        status_resp = requests.get(status_url, headers=headers)
        status_resp.raise_for_status()
        final_data = status_resp.json()

        status = final_data.get("status")
        if status in ["COMPLETED", "FAILED", "CANCELLED"]:
            break

        time.sleep(2)

    # 3) Extraire seulement le texte utile
    answer = "Je n'ai pas trouvé de réponse."

    if final_data and "attachments" in final_data:
        for attachment in final_data["attachments"]:
            if "text" in attachment and "content" in attachment["text"]:
                answer = attachment["text"]["content"]
                break

    return jsonify({
        "answer": answer,
        "status": final_data.get("status"),
        "conversation_id": conversation_id,
        "message_id": message_id
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
