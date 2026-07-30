#!/bin/bash
# Deploy the current main branch on the server.
#
# Run on the box:  ~/dott_landing/deploy/deploy.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/dott_landing}"
cd "$APP_DIR"

echo "==> Fetching"
git fetch --quiet origin
git checkout --quiet main
git pull --ff-only origin main

echo "==> Dependencies"
if [ ! -x venv/bin/python ]; then
  echo "    venv missing or broken - rebuilding"
  rm -rf venv
  python3 -m venv venv
fi
venv/bin/pip install --quiet --upgrade pip
venv/bin/pip install --quiet -r requirements.txt

echo "==> Checking configuration"
if [ ! -f .env ]; then
  echo "    WARNING: no .env - the admin panel will stay disabled."
  echo "    Create it from .env.example, then run tools/hash_password.py"
else
  chmod 600 .env
fi

echo "==> Database directory"
sudo mkdir -p /var/lib/dott
sudo chown ubuntu:ubuntu /var/lib/dott
sudo chmod 700 /var/lib/dott

echo "==> Import check"
venv/bin/python -c "import app" >/dev/null

echo "==> Restarting"
sudo systemctl restart dott
sleep 2
systemctl is-active --quiet dott && echo "    dott is running" || {
  echo "    dott FAILED to start:"
  sudo journalctl -u dott -n 30 --no-pager
  exit 1
}

echo "==> Smoke test"
code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/)
echo "    GET / -> $code"
[ "$code" = "200" ] || exit 1

echo "==> Done. Deployed $(git rev-parse --short HEAD)"
