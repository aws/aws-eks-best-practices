#! /usr/bin/env bash

# This script helps run the docker container locally instead of in GH Actions

TEMPDIR="$(mktemp -d)"
REPO_URL="https://github.com/aws/aws-eks-best-practices"

git clone "$REPO_URL" "$TEMPDIR"

docker run -it \
  -v "${TEMPDIR}:/opt/repo" \
  -e LINKBOT_REPO_ROOT=/opt/repo \
  -e LINKBOT_REPO_URL="$REPO_URL" \
  -e LINKBOT_GLOB="content/security/docs/*.md" \
  -e LINKBOT_MAX_DAYS_OLD=730 \
  -e LINKBOT_GH_USER \
  -e LINKBOT_GH_TOKEN \
  -e LINKBOT_DRY_RUN=true \
  linkbot:latest