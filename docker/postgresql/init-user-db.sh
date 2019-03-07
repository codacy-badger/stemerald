#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER dev;
    CREATE DATABASE stemerald_db;
    GRANT ALL PRIVILEGES ON DATABASE stemerald_db TO dev;
    ALTER USER dev WITH PASSWORD 'dev-secret    ';
EOSQL