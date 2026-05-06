#!/bin/bash
set -e

cd "$(dirname "$0")/.."

if [ ! -f ".env" ]; then
  echo "No .env file found. Copy .env.sample to .env and fill in values."
  exit 1
fi

set -a
source .env
set +a

export MONGO_URI="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@${MONGO_HOSTS}/${MONGO_DB_NAME}${MONGO_OPTIONS}"

echo "Starting MongoDB..."
docker compose -f docker-compose.dev.yml up -d

echo ""
echo "What to run? (1) bot [default]  (2) web"
read -rp "... " mode

if [ "${mode}" == "2" ]; then
  python3 -m app --web
else
  python3 -m app --telegram-bot
fi
