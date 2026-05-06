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

export MONGO_URI="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@ihd-mongo:27017/${MONGO_DB_NAME}${MONGO_OPTIONS}"

echo "Build tool: (1) docker [default]  (2) podman"
read -rp "... " tool_id
[ "${tool_id}" == "2" ] && cmd=podman || cmd=docker

echo "Building images..."
${cmd} compose -f docker-compose.prod.yml build

echo "Starting services..."
${cmd} compose -f docker-compose.prod.yml up -d

echo ""
echo "Services started. Useful commands:"
echo "  ${cmd} compose -f docker-compose.prod.yml logs -f"
echo "  ${cmd} compose -f docker-compose.prod.yml down"
