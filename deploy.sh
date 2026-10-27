#!/usr/bin/env bash
set -Eeuo pipefail

LOG_FILE="$HOME/oil-prices-map/deploy.log"
ERROR_LOG_FILE="$HOME/oil-prices-map/deploy-error.log"
WEB_ROOT="/var/www/oil-prices-map"
BACKUP_DIR="$HOME/oil-prices-map/backups"
TIMESTAMP="$(date +%F-%H%M%S)"

on_error() {
  local rc=$?
  echo "[$(date '+%F %T')] deploy failed with exit code $rc"
  exit "$rc"
}

mkdir -p "$BACKUP_DIR"
mkdir -p "$WEB_ROOT"
mkdir -p "$(dirname "$LOG_FILE")"

exec >> "$LOG_FILE" 2>> "$ERROR_LOG_FILE"

trap on_error ERR

echo "[$(date '+%F %T')] deploy started"

cd "$HOME/oil-prices-map"

if [ ! -d .venv ]; then
  echo "[$(date '+%F %T')] creating virtualenv"
  python3 -m venv .venv
fi

. .venv/bin/activate

echo "[$(date '+%F %T')] installing dependencies"
python -m pip install -r requirements.txt

echo "[$(date '+%F %T')] pulling latest code"
git pull --ff-only origin main

echo "[$(date '+%F %T')] downloading latest SPIMEX PDF"
python scripts/download_spimex.py --save-dir pdf_data

echo "[$(date '+%F %T')] generating map"
python main.py

if [ -f "$WEB_ROOT/index.html" ]; then
  cp "$WEB_ROOT/index.html" "$BACKUP_DIR/index-$TIMESTAMP.html"
  echo "[$(date '+%F %T')] backup created: $BACKUP_DIR/index-$TIMESTAMP.html"
fi

echo "[$(date '+%F %T')] publishing files"
cp -a public/. "$WEB_ROOT/"
chmod -R 755 "$WEB_ROOT"

echo "[$(date '+%F %T')] deploy complete: $WEB_ROOT/index.html"
