import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _bool(name, default):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# --- email ---------------------------------------------------------------
# Submissions are stored in the database first, so email is a best-effort
# notification. Disabled by default: it needs a credential that storage does
# not, and a missing credential must not look like a working setup.
EMAIL_ENABLED = _bool("EMAIL_ENABLED", "false")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = _bool("EMAIL_USE_TLS", "true")
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
WAITLIST_SUBJECT = os.getenv("WAITLIST_SUBJECT", "New Dott Health waitlist signup")
REGISTER_SUBJECT = os.getenv(
    "REGISTER_SUBJECT", "New Dott Health practitioner registration"
)

# --- database ------------------------------------------------------------
# Production sets this to /var/lib/dott/dott.db, outside the repo so it can
# never be committed. *.db is gitignored regardless.
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "dott.db"))
DB_TIMEOUT = float(os.getenv("DB_TIMEOUT", "5"))

# --- admin ---------------------------------------------------------------
# A PBKDF2 hash, never the password itself: a leaked .env then yields
# something an attacker still cannot log in with. Generate with
# `python tools/hash_password.py`.
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")

# Idle timeout; the cookie also carries an absolute cap below.
SESSION_IDLE_MINUTES = int(os.getenv("SESSION_IDLE_MINUTES", "30"))
SESSION_ABSOLUTE_HOURS = int(os.getenv("SESSION_ABSOLUTE_HOURS", "12"))

# False only for local http development - a Secure cookie is not sent over
# plain http, which would make local login impossible.
SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", "true")

# Per-IP login throttle. Deliberately not a global lockout: that would let
# anyone lock the team out of their own dashboard.
LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
LOGIN_WINDOW_MINUTES = int(os.getenv("LOGIN_WINDOW_MINUTES", "15"))

# Optional extra hardening: comma separated IPs or CIDR-less prefixes that may
# reach /nimda at all. Empty means no IP restriction.
ADMIN_IP_ALLOWLIST = [
    entry.strip()
    for entry in os.getenv("ADMIN_IP_ALLOWLIST", "").split(",")
    if entry.strip()
]

# --- public form throttle ------------------------------------------------
FORM_MAX_SUBMISSIONS = int(os.getenv("FORM_MAX_SUBMISSIONS", "10"))
FORM_WINDOW_MINUTES = int(os.getenv("FORM_WINDOW_MINUTES", "60"))

# Number of reverse proxies in front of the app. nginx sets X-Forwarded-For,
# and this must match reality: too high lets a client spoof its own IP and
# evade the rate limits.
TRUSTED_PROXY_HOPS = int(os.getenv("TRUSTED_PROXY_HOPS", "1"))
