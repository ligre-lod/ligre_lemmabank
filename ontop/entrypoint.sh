#!/bin/sh
set -e

: "${LIGRE_BASE_URL:=https://dev.ligre.ugent.be}"

cat /opt/ontop/input/mapping.ttl.template /opt/ontop/input/corpora/*.ttl.template \
  | sed "s|__LIGRE_BASE_URL__|${LIGRE_BASE_URL}|g" > /tmp/mapping.ttl

export ONTOP_MAPPING_FILE=/tmp/mapping.ttl

exec /opt/ontop/entrypoint.sh "$@"
