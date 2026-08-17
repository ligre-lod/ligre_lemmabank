FROM ontop/ontop:5.5.0

# Bake the ontop configuration (mapping, ontology, properties) and the
# JDBC driver into the image.
COPY input/mapping.ttl /opt/ontop/input/mapping.ttl
COPY input/ontology.ttl /opt/ontop/input/ontology.ttl
COPY input/ontop.properties /opt/ontop/input/ontop.properties
COPY jdbc/ /opt/ontop/jdbc/
