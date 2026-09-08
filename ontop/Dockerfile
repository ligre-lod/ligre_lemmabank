FROM ontop/ontop:5.5.0

COPY input/mapping.ttl.template /opt/ontop/input/mapping.ttl.template
COPY input/ontop.properties /opt/ontop/input/ontop.properties
COPY jdbc/ /opt/ontop/jdbc/
COPY entrypoint.sh /opt/ontop/ligre-entrypoint.sh

ENTRYPOINT ["/opt/ontop/ligre-entrypoint.sh"]
CMD ["./ontop", "endpoint"]
