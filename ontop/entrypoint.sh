#!/bin/sh
set -e

: "${LIGRE_BASE_URL:=https://w3id.org/ligre}"

sed "s|__LIGRE_BASE_URL__|${LIGRE_BASE_URL}|g" \
  /opt/ontop/input/mapping.ttl.template > /tmp/mapping.ttl

export ONTOP_MAPPING_FILE=/tmp/mapping.ttl

facts=""
if [ -n "${ONTOP_FACTS_FILE:-}" ] && [ -f "${ONTOP_FACTS_FILE}" ]; then
  facts="${ONTOP_FACTS_FILE}"
fi
if [ -n "${ONTOP_LINKSETS_DIRECTORY:-}" ] && [ -d "${ONTOP_LINKSETS_DIRECTORY}" ]; then
  for linkset in "${ONTOP_LINKSETS_DIRECTORY}"/*.ttl; do
    case "${linkset}" in *_description.ttl) continue ;; esac
    if [ -f "${linkset}" ]; then
      facts="${facts} ${linkset}"
    fi
  done
fi

if [ -n "${facts}" ]; then
  for file in ${facts}; do
    cat "${file}"
    echo
  done | sed "s|https://w3id.org/ligre/|${LIGRE_BASE_URL}/|g" > /tmp/facts.ttl
  export ONTOP_FACTS_FILE=/tmp/facts.ttl
fi

exec /opt/ontop/entrypoint.sh "$@"
