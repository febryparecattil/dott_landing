#!/usr/bin/env python
"""Generate the ADMIN_PASSWORD_HASH and SECRET_KEY values for .env.

Run on the server so the password never travels anywhere:

    venv/bin/python tools/hash_password.py

The password is read from a hidden prompt, never from argv - anything passed
as an argument would land in shell history and the process list.
"""
import getpass
import secrets
import sys

from werkzeug.security import generate_password_hash

# PBKDF2-SHA256 rather than scrypt: available on every build of Python, and
# the same hash then verifies on both the server and a developer machine.
METHOD = "pbkdf2:sha256:600000"
MIN_LENGTH = 12


def main():
    password = getpass.getpass("Admin password: ")
    if len(password) < MIN_LENGTH:
        sys.exit("Too short - use at least %d characters." % MIN_LENGTH)
    if password != getpass.getpass("Confirm: "):
        sys.exit("Passwords did not match.")

    # Single quoted: the hash contains '$' separators, which an unquoted shell
    # heredoc or `echo` would happily expand into nothing.
    print("\nAdd these two lines to .env:\n")
    print("ADMIN_PASSWORD_HASH='%s'" % generate_password_hash(password, method=METHOD))
    print("SECRET_KEY='%s'" % secrets.token_urlsafe(48))
    print("\nThen: chmod 600 .env && sudo systemctl restart dott")


if __name__ == "__main__":
    main()
