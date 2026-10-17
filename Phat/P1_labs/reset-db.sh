#!/usr/bin/env bash
# reset-db.sh - Khoi phuc CSDL EShop ve trang thai sach sau khi test Lab 2 (SQLi).
# Dung ban sao luu backend/database.sqlite.bak de ghi de backend/database.sqlite.
# Chay tu thu muc goc eshop-sut:  bash Phat/P1_labs/reset-db.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DB="$ROOT/backend/database.sqlite"
BACKUP="$ROOT/backend/database.sqlite.bak"

if [ ! -f "$BACKUP" ]; then
  echo "Khong tim thay ban sao luu: $BACKUP" >&2
  echo "Hay tao bang: cp \"$DB\" \"$BACKUP\" TRUOC khi test." >&2
  exit 1
fi

cp -f "$BACKUP" "$DB"
echo "Da khoi phuc database.sqlite tu database.sqlite.bak."
echo "Luu y: khoi dong lai backend (npm start trong backend/) de nap lai CSDL sach."
