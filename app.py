import csv
import functools
import hmac
import io
import json
import logging
import secrets
import smtplib
import time
from datetime import timedelta
from email.message import EmailMessage

from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash

import db
import settings

app = Flask(__name__)

# nginx terminates TLS and sets X-Forwarded-For / -Proto. Without this,
# every client looks like 127.0.0.1 - which would make the per-IP rate
# limits useless and lock everyone out at once.
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=settings.TRUSTED_PROXY_HOPS,
    x_proto=settings.TRUSTED_PROXY_HOPS,
    x_host=settings.TRUSTED_PROXY_HOPS,
)

# The admin panel is only available when both secrets are configured. A
# default or generated SECRET_KEY would let anyone forge a session cookie,
# so an unconfigured deployment serves the public site and nothing else.
ADMIN_CONFIGURED = bool(settings.SECRET_KEY and settings.ADMIN_PASSWORD_HASH)
app.secret_key = settings.SECRET_KEY or secrets.token_hex(32)

app.config.update(
    SESSION_COOKIE_NAME="dott_admin",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=settings.SESSION_COOKIE_SECURE,
    SESSION_COOKIE_SAMESITE="Strict",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=settings.SESSION_IDLE_MINUTES),
    MAX_CONTENT_LENGTH=64 * 1024,
)

if not app.debug:
    logging.basicConfig(level=logging.INFO)

if not ADMIN_CONFIGURED:
    app.logger.warning(
        "Admin panel disabled: SECRET_KEY and ADMIN_PASSWORD_HASH must both be set."
    )
elif len(settings.SECRET_KEY) < 32:
    app.logger.warning(
        "SECRET_KEY is shorter than 32 characters - generate a longer one."
    )

try:
    db.init()
except Exception:
    app.logger.exception("Database initialisation failed")

PER_PAGE = 50

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
    "We couldn't save your details right now. Please try again, "
    "or email us at hello@dott.health."
)
TOO_MANY = "Too many submissions from this connection. Please try again later."


# --- helpers -------------------------------------------------------------

def client_ip():
    return request.remote_addr or "unknown"


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
        app.logger.info("Email disabled - stored only. Submission:\n%s", body)
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


def form_rate_limited(kind):
    bucket = "form:%s:%s" % (kind, client_ip())
    seen = db.hit(bucket, settings.FORM_WINDOW_MINUTES * 60)
    return seen > settings.FORM_MAX_SUBMISSIONS


def handle_submission(kind, data, store, subject, success_message):
    """Store first, then notify. Storage is what must not fail."""
    try:
        store(data, client_ip())
    except Exception:
        app.logger.exception("%s could not be stored", kind)
        return jsonify({"message": SUBMISSION_FAILED}), 500

    # The row is safely on disk, so a failed notification is a warning, not a
    # lost submission - the response can honestly report success.
    try:
        send_notification(subject, data)
    except Exception:
        app.logger.exception("%s stored but notification failed", kind)

    return jsonify({"message": success_message})


# --- csrf ----------------------------------------------------------------

def csrf_token():
    token = session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf"] = token
    return token


def csrf_valid():
    expected = session.get("csrf", "")
    submitted = request.form.get("csrf_token", "")
    return bool(expected) and hmac.compare_digest(str(expected), str(submitted))


@app.context_processor
def inject_csrf():
    return {"csrf_token": csrf_token}


# --- admin auth ----------------------------------------------------------

def ip_allowed():
    if not settings.ADMIN_IP_ALLOWLIST:
        return True
    ip = client_ip()
    return any(ip == entry or ip.startswith(entry) for entry in settings.ADMIN_IP_ALLOWLIST)


def session_valid():
    if not session.get("admin"):
        return False
    started = session.get("login_at", 0)
    if time.time() - float(started) > settings.SESSION_ABSOLUTE_HOURS * 3600:
        session.clear()
        return False
    return True


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not ADMIN_CONFIGURED or not ip_allowed():
            # Do not confirm the panel exists to someone who cannot use it.
            abort(404)
        if not session_valid():
            return redirect(url_for("admin_login"))
        session.permanent = True
        return view(*args, **kwargs)

    return wrapped


def login_locked_out():
    bucket = "login_fail:%s" % client_ip()
    seen = db.count_in_window(bucket, settings.LOGIN_WINDOW_MINUTES * 60)
    return seen >= settings.LOGIN_MAX_FAILURES


@app.route("/nimda", methods=["GET", "POST"])
def admin_login():
    if not ADMIN_CONFIGURED or not ip_allowed():
        abort(404)

    if session_valid():
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        if not csrf_valid():
            error = "Your session expired. Please try again."
        elif login_locked_out():
            db.audit("login_locked_out", client_ip())
            error = "Too many attempts. Please try again later."
        elif check_password_hash(
            settings.ADMIN_PASSWORD_HASH, request.form.get("password", "")
        ):
            db.clear_bucket("login_fail:%s" % client_ip())
            db.audit("login_success", client_ip())
            # New session id and token on login, to defeat session fixation.
            session.clear()
            session["admin"] = True
            session["login_at"] = time.time()
            session["csrf"] = secrets.token_urlsafe(32)
            session.permanent = True
            return redirect(url_for("admin_dashboard"))
        else:
            db.hit("login_fail:%s" % client_ip(), settings.LOGIN_WINDOW_MINUTES * 60)
            db.audit("login_failure", client_ip())
            error = "Incorrect password."

    return render_template("admin/login.html", error=error), (
        200 if error is None else 401
    )


@app.route("/nimda/logout", methods=["POST"])
@login_required
def admin_logout():
    if not csrf_valid():
        abort(400)
    db.audit("logout", client_ip())
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/nimda/dashboard")
@login_required
def admin_dashboard():
    table = request.args.get("table", "registrations")
    if table not in ("registrations", "waitlist"):
        table = "registrations"

    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1

    rows = db.recent(table, limit=PER_PAGE, offset=(page - 1) * PER_PAGE)
    for row in rows:
        if row.get("extra"):
            try:
                row["extra_parsed"] = json.loads(row["extra"])
            except (TypeError, ValueError):
                row["extra_parsed"] = {}
        else:
            row["extra_parsed"] = {}

    total = db.count(table)
    return render_template(
        "admin/dashboard.html",
        table=table,
        rows=rows,
        page=page,
        per_page=PER_PAGE,
        total=total,
        has_next=page * PER_PAGE < total,
        counts={
            "registrations": db.count("registrations"),
            "waitlist": db.count("waitlist"),
        },
        audit=db.recent_audit(10),
        label_for=label_for,
    )


def csv_safe(value):
    """Defuse spreadsheet formula injection before Excel or Sheets sees it."""
    text = "" if value is None else str(value)
    if text[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


@app.route("/nimda/export/<table>.csv")
@login_required
def admin_export(table):
    if table not in ("registrations", "waitlist"):
        abort(404)

    rows = db.all_rows(table)
    buffer = io.StringIO()

    if rows:
        columns = list(rows[0].keys())
        writer = csv.writer(buffer)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([csv_safe(row.get(column)) for column in columns])
    else:
        buffer.write("no rows\n")

    db.audit("export", client_ip(), detail=table)
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="dott-%s.csv"' % table,
            "Cache-Control": "no-store, max-age=0",
        },
    )


# --- public --------------------------------------------------------------

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

    if form_rate_limited("waitlist"):
        return jsonify({"message": TOO_MANY}), 429

    return handle_submission(
        "Waitlist signup",
        data,
        db.insert_waitlist,
        settings.WAITLIST_SUBJECT,
        "Thank you {}! You have joined the waitlist.".format(name),
    )


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

    if form_rate_limited("register"):
        return jsonify({"message": TOO_MANY}), 429

    return handle_submission(
        "Registration",
        data,
        db.insert_registration,
        settings.REGISTER_SUBJECT,
        "Welcome aboard {}! Our team will reach out shortly.".format(name),
    )


# --- responses -----------------------------------------------------------

@app.errorhandler(413)
def too_large(_error):
    return jsonify({"message": "Submission too large."}), 413


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Frame-Options", "DENY")
    if request.is_secure:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )

    if request.path.startswith("/nimda"):
        # Personal data: keep it out of caches, proxies and search engines.
        response.headers["Cache-Control"] = "no-store, max-age=0, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'self'; img-src 'self' data:; "
            "form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
        )

    return response


if __name__ == "__main__":
    app.run(debug=True)
