import os

from dotenv import load_dotenv

load_dotenv()

# Defaults to true so a missing .env fails loudly instead of silently
# accepting submissions and dropping them.
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "") or EMAIL_USERNAME
EMAIL_RECIPIENTS = [
    address.strip()
    for address in os.getenv(
        "EMAIL_RECIPIENTS",
        "subin@dott.health,febry@dott.health,jithu@dott.health",
    ).split(",")
    if address.strip()
]
WAITLIST_SUBJECT = os.getenv(
    "WAITLIST_SUBJECT", "New Dott Health waitlist signup"
)
REGISTER_SUBJECT = os.getenv(
    "REGISTER_SUBJECT", "New Dott Health practitioner registration"
)
