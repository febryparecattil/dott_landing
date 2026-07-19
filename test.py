import smtplib

EMAIL = "febry@dott.health"
APP_PASSWORD = "jvfm awhj dbkx bzas"

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, APP_PASSWORD)
    print("✅ Login successful!")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print("❌ Authentication failed")
    print(e)
except Exception as e:
    print("❌ Error:", e)
