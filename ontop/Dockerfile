# Built from the repository root: docker build -f ontop/Dockerfile .
FROM ontop/ontop:5.5.0

COPY ontop/input/mapping.ttl.template /opt/ontop/input/mapping.ttl.template
COPY ontop/input/ontop.properties /opt/ontop/input/ontop.properties
COPY ontop/jdbc/ /opt/ontop/jdbc/
COPY ontop/entrypoint.sh /opt/ontop/ligre-entrypoint.sh

# Static facts served next to the mapped lemmas: the VoID/DCAT descriptions of
# the knowledge base, the lemma bank and the corpora, so that their IRIs resolve.
COPY ttl/ligre_void.ttl /opt/ontop/facts/ligre_void.ttl
ENV ONTOP_FACTS_FILE=/opt/ontop/facts/ligre_void.ttl \
    ONTOP_FACTS_FORMAT=turtle

ENTRYPOINT ["/opt/ontop/ligre-entrypoint.sh"]
CMD ["./ontop", "endpoint"]
