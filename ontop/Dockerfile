FROM ontop/ontop:5.5.0

COPY ontop/input/mapping.ttl.template /opt/ontop/input/mapping.ttl.template
COPY ontop/input/ontop.properties /opt/ontop/input/ontop.properties
COPY ontop/jdbc/ /opt/ontop/jdbc/
COPY ontop/entrypoint.sh /opt/ontop/ligre-entrypoint.sh

COPY ttl/ligre_void.ttl /opt/ontop/facts/ligre_void.ttl
COPY ttl/linksets/ /opt/ontop/facts/linksets/
ENV ONTOP_FACTS_FILE=/opt/ontop/facts/ligre_void.ttl \
    ONTOP_LINKSETS_DIRECTORY=/opt/ontop/facts/linksets \
    ONTOP_FACTS_FORMAT=turtle

ENTRYPOINT ["/opt/ontop/ligre-entrypoint.sh"]
CMD ["./ontop", "endpoint"]
