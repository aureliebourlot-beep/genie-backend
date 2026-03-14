from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "HELLO OK"

@app.route("/test", methods=["POST"])
def test():
    data = request.get_json()

    question = data.get("message")

    return jsonify({
        "answer": f"Tu as envoyé: {question}"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
