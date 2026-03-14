from flask import Flask, request, jsonify
import os
import requests

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

    url = f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/start-conversation"

    response = requests.post(url, headers=headers, json={
        "content": question
    })

    return jsonify(response.json())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
