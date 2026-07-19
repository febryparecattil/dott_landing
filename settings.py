import os

EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@dott.health")
EMAIL_RECIPIENTS = [
    address.strip()
    for address in os.getenv(
        "EMAIL_RECIPIENTS",
        "subin@dott.health,febry@dott.health,jithu@dott.health",
    ).split(",")
    if address.strip()
]
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "New Dott Health waitlist signup")
