from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/join-waitlist", methods=["POST"])
def join_waitlist():
    data = request.get_json()
    return jsonify({
        "message": f"Thank you {data.get('name', '')}! You have joined the waitlist."
    })

if __name__ == "__main__":
    app.run(debug=True)
