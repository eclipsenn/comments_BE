FROM postgres:9.6

COPY create_tables.sql /docker-entrypoint-initdb.d/create_tables.sql
COPY examples.sql /docker-entrypoint-initdb.d/examples.sql