import os
import smtplib
from email.message import EmailMessage

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def send_simple_email(data):
    smtp_username = "febry@dott.health"
    smtp_password = os.getenv("SMTP_PASSWORD", "")

    recipients = ["subin@dott.health", "febry@dott.health", "jithu@dott.health"]

    msg = EmailMessage()
    msg["Subject"] = "New waitlist submission"
    msg["From"] = smtp_username
    msg["To"] = ", ".join(recipients)

    body = "\n".join(
        [f"{key}: {value}" for key, value in data.items() if value]
    )
    msg.set_content(body or "No data provided")

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(msg)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/join-waitlist", methods=["POST"])
def join_waitlist():
    data = request.get_json(silent=True) or {}
    try:
        send_simple_email(data)
    except Exception:
        pass

    return jsonify({
        "message": f"Thank you {data.get('name', '')}! You have joined the waitlist."
    })


if __name__ == "__main__":
    app.run(debug=True)
