#!/bin/sh
set -e

# Deployed images mint persistent w3id IRIs; docker-compose.yml overrides this
# with the local LodView address for local development.
: "${LIGRE_BASE_URL:=https://w3id.org/ligre}"

sed "s|__LIGRE_BASE_URL__|${LIGRE_BASE_URL}|g" \
  /opt/ontop/input/mapping.ttl.template > /tmp/mapping.ttl

export ONTOP_MAPPING_FILE=/tmp/mapping.ttl

exec /opt/ontop/entrypoint.sh "$@"
