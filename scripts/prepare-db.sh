#!/usr/bin/env bash

cd scripts
source variables.sh

echo "CREATE USER ${DB_USERNAME}" | sudo -u postgres psql
echo "CREATE DATABASE ${DB_NAME}" | sudo -u postgres psql
echo "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USERNAME}" | sudo -u postgres psql
echo "ALTER USER ${DB_USERNAME} WITH PASSWORD '${DB_PASSWORD}'" | sudo -u postgres psql

echo "
source variables.sh;
source \$(which virtualenvwrapper.sh);
workon ${VIRTUALENV_NAME};
${EMERALD} admin setup-db
" | sudo -EHsu ${SERVICE_USER}