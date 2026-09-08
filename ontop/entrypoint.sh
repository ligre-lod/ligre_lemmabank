#!/bin/sh
set -e

: "${LIGRE_BASE_URL:=https://dev.ligre.ugent.be}"

sed "s|__LIGRE_BASE_URL__|${LIGRE_BASE_URL}|g" \
  /opt/ontop/input/mapping.ttl.template > /tmp/mapping.ttl

export ONTOP_MAPPING_FILE=/tmp/mapping.ttl

exec /opt/ontop/entrypoint.sh "$@"
