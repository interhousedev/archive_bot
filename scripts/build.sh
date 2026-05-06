#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "Build tool: (1) docker [default]  (2) podman"
read -rp "... " tool_id
[ "${tool_id}" == "2" ] && cmd=podman || cmd=docker

echo "What to build: (1) bot [default]  (2) web  (3) both"
read -rp "... " target

build_bot=false
build_web=false
[ "${target}" == "2" ] && build_web=true
[ "${target}" == "3" ] && build_bot=true && build_web=true
[ "${target}" == "1" ] || [ -z "${target}" ] && build_bot=true

if $build_bot; then
  echo "Building ihd-bot..."
  ${cmd} build --platform linux/amd64 -f Dockerfile.bot -t  \
   ghcr.io/interhousedev/archive_bot:bot-latest .
  echo "ihd-bot built."
fi

if $build_web; then
  echo "Building ihd-web..."
  ${cmd} build --platform linux/amd64 -f Dockerfile.web -t \
   ghcr.io/interhousedev/archive_bot:web-latest .
  echo "ihd-web built."
fi

${cmd} push ghcr.io/interhousedev/archive_bot:web-latest
${cmd} push ghcr.io/interhousedev/archive_bot:bot-latest
