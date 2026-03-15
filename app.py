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

    # 1) Démarrer une conversation avec la question
    start_url = f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/start-conversation"

    start_resp = requests.post(
        start_url,
        headers=headers,
        json={"content": question}
    )

    try:
        start_resp.raise_for_status()
    except requests.exceptions.HTTPError:
        return jsonify({
            "error": "Erreur lors du start-conversation",
            "details": start_resp.text
        }), start_resp.status_code

    start_data = start_resp.json()

    conversation_id = start_data.get("conversation_id")
    message_id = start_data.get("message_id")

    if not conversation_id or not message_id:
        return jsonify({
            "error": "conversation_id ou message_id manquant",
            "start_response": start_data
        }), 500

    # 2) Polling du message jusqu'à completion
    status_url = (
        f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}"
        f"/conversations/{conversation_id}/messages/{message_id}"
    )

    final_data = None

    for _ in range(20):
        status_resp = requests.get(status_url, headers=headers)

        try:
            status_resp.raise_for_status()
        except requests.exceptions.HTTPError:
            return jsonify({
                "error": "Erreur lors de la récupération du message Genie",
                "details": status_resp.text,
                "conversation_id": conversation_id,
                "message_id": message_id
            }), status_resp.status_code

        final_data = status_resp.json()
        status = final_data.get("status")

        if status == "COMPLETED":
            break

        if status in ["FAILED", "CANCELLED"]:
            return jsonify({
                "error": "Le message Genie a échoué",
                "conversation_id": conversation_id,
                "message_id": message_id,
                "result": final_data
            }), 500

        time.sleep(2)

    if not final_data:
        return jsonify({
            "error": "Aucune réponse récupérée depuis Genie",
            "conversation_id": conversation_id,
            "message_id": message_id
        }), 500

    # 3) Extraire le meilleur texte possible
    answer = None
    suggested_questions = []

    attachments = final_data.get("attachments", [])

    for attachment in attachments:
        if "text" in attachment:
            text_block = attachment.get("text", {})
            content = text_block.get("content")
            if content:
                answer = content
                break

    for attachment in attachments:
        if "suggested_questions" in attachment:
            sq = attachment.get("suggested_questions", {})
            questions = sq.get("questions", [])
            if questions:
                suggested_questions = questions

    # 4) Fallback si aucun texte n'a été trouvé
    if not answer:
        answer = final_data.get("content")

    if not answer:
        answer = "Je n'ai pas trouvé de réponse exploitable."

    return jsonify({
        "answer": answer,
        "status": final_data.get("status"),
        "conversation_id": conversation_id,
        "message_id": message_id,
        "suggested_questions": suggested_questions,
        "raw_result": final_data
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
