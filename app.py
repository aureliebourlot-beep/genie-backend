from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID")

HEADERS = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
    "Content-Type": "application/json"
}

@app.route("/")
def home():
    return "Backend Genie OK"

@app.route("/genie/start", methods=["POST"])
def genie_start():
    url = f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/start-conversation"
    response = requests.post(url, headers=HEADERS, json={})
    response.raise_for_status()
    data = response.json()
    return jsonify(data)

@app.route("/genie/message", methods=["POST"])
def genie_message():
    body = request.get_json()
    conversation_id = body.get("conversation_id")
    message = body.get("message")

    if not conversation_id or not message:
        return jsonify({"error": "conversation_id et message sont requis"}), 400

    create_url = f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/{conversation_id}/messages"
    create_payload = {
        "content": message
    }

    create_resp = requests.post(create_url, headers=HEADERS, json=create_payload)
    create_resp.raise_for_status()
    create_data = create_resp.json()

    message_id = create_data.get("message_id")
    if not message_id:
        return jsonify({
            "error": "message_id introuvable dans la réponse Databricks",
            "create_response": create_data
        }), 500

    status_url = f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/{conversation_id}/messages/{message_id}"

    final_data = None
    for _ in range(20):
        status_resp = requests.get(status_url, headers=HEADERS)
        status_resp.raise_for_status()
        final_data = status_resp.json()

        status = final_data.get("status")
        if status in ["COMPLETED", "FAILED", "CANCELLED"]:
            break

        time.sleep(2)

    return jsonify({
        "conversation_id": conversation_id,
        "message_id": message_id,
        "result": final_data
    })

if __name__ == "__main__":
    app.run(debug=True)