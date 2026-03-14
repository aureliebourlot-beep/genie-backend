from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "HELLO OK"

@app.route("/test")
def test():
    message = request.args.get("message")

    return jsonify({
        "answer": f"Tu as envoyé: {message}"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
