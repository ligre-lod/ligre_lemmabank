#!/bin/sh
set -e

: "${LIGRE_BASE_URL:=https://w3id.org/ligre}"

sed "s|__LIGRE_BASE_URL__|${LIGRE_BASE_URL}|g" \
  /opt/ontop/input/mapping.ttl.template > /tmp/mapping.ttl

export ONTOP_MAPPING_FILE=/tmp/mapping.ttl

if [ -n "${ONTOP_FACTS_FILE:-}" ] && [ -f "${ONTOP_FACTS_FILE}" ]; then
  sed "s|https://w3id.org/ligre/|${LIGRE_BASE_URL}/|g" "${ONTOP_FACTS_FILE}" > /tmp/facts.ttl
  export ONTOP_FACTS_FILE=/tmp/facts.ttl
fi

exec /opt/ontop/entrypoint.sh "$@"
