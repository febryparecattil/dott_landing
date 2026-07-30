import logging
import smtplib
from email.message import EmailMessage

from flask import Flask, render_template, request, jsonify

import settings

app = Flask(__name__)

if not app.debug:
    logging.basicConfig(level=logging.INFO)

FIELD_LABELS = {
    "name": "Name",
    "email": "Email",
    "phone": "Phone",
    "mobile": "Mobile",
    "whatsapp": "Has WhatsApp",
    "profession": "Profession",
    "city": "City",
    "state": "State",
    "license": "Registration number",
    "qualification": "Qualification",
    "specialty": "Specialty",
    "experience": "Experience",
    "workplace": "Current hospital/clinic",
    "employer": "Current employer",
    "district-city": "District/City",
    "working-area": "Working area",
    "services": "Services",
    "nursing-services": "Nursing services",
    "mode": "Consultation mode",
    "days": "Available days",
    "shift": "Preferred shift",
    "willing-to-travel": "Willing to travel",
    "languages": "Languages",
}

SUBMISSION_FAILED = (
    "We couldn't submit your details right now. Please try again, "
    "or email us at hello@dott.health."
)


def label_for(key):
    return FIELD_LABELS.get(key, key.replace("-", " ").replace("_", " ").capitalize())


def format_body(data):
    """Render a submission as 'Label: value' lines, skipping empty fields."""
    lines = []
    for key, value in data.items():
        if isinstance(value, bool):
            value = "Yes" if value else "No"
        elif isinstance(value, list):
            value = ", ".join(str(item).strip() for item in value if str(item).strip())
        elif value is None:
            value = ""
        else:
            value = str(value).strip()

        if not value:
            continue
        lines.append("{}: {}".format(label_for(key), value))

    return "\n".join(lines)


def send_notification(subject, data):
    body = format_body(data)
    if not body:
        raise ValueError("submission contained no usable fields")

    if not settings.EMAIL_ENABLED:
        app.logger.warning(
            "EMAIL_ENABLED is false - not sending. Submission was:\n%s", body
        )
        return

    if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
        raise RuntimeError(
            "EMAIL_USERNAME/EMAIL_PASSWORD are not configured - see .env.example"
        )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = ", ".join(settings.EMAIL_RECIPIENTS)
    msg["Reply-To"] = str(data.get("email", "")).strip() or settings.EMAIL_FROM
    msg.set_content(body)

    with smtplib.SMTP(
        settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT
    ) as smtp:
        if settings.EMAIL_USE_TLS:
            smtp.starttls()
        smtp.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        smtp.send_message(msg)

    app.logger.info("Sent '%s' to %s", subject, ", ".join(settings.EMAIL_RECIPIENTS))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/join-waitlist", methods=["POST"])
def join_waitlist():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    if not name or not email:
        return jsonify({"message": "Please provide your name and email address."}), 400

    try:
        send_notification(settings.WAITLIST_SUBJECT, data)
    except Exception:
        app.logger.exception("Waitlist notification failed")
        return jsonify({"message": SUBMISSION_FAILED}), 502

    return jsonify({
        "message": "Thank you {}! You have joined the waitlist.".format(name)
    })


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    mobile = str(data.get("mobile", "")).strip()
    if not name or not email or not mobile:
        return jsonify({
            "message": "Please provide your name, mobile number and email address."
        }), 400

    try:
        send_notification(settings.REGISTER_SUBJECT, data)
    except Exception:
        app.logger.exception("Registration notification failed")
        return jsonify({"message": SUBMISSION_FAILED}), 502

    return jsonify({
        "message": "Welcome aboard {}! Our team will reach out shortly.".format(name)
    })


if __name__ == "__main__":
    app.run(debug=True)
