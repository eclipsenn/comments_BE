#!/usr/bin/env bash
psql -U postgres -c "DROP DATABASE IF EXISTS comments_db"
psql -U postgres  -c "DROP ROLE IF EXISTS exness"
psql -U postgres  -c "CREATE USER exness WITH PASSWORD 'exness';"
psql -U postgres -c "CREATE DATABASE comments_db ENCODING 'UTF8';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE comments_db TO exness;"

cat sql/create_tables.sql | psql -U postgres -d comments_db -a
cat sql/examples.sql | psql -U postgres -d comments_db -a