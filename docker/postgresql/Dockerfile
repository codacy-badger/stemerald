FROM postgres:9

COPY init-user-db.sh /docker-entrypoint-initdb.d/init-user-db.sh

# RUN echo "CREATE USER ${DB_USERNAME}" | psql && \
#     echo "CREATE DATABASE ${DB_NAME}" | psql && \
#     echo "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USERNAME}" | psql && \
#     echo "ALTER USER ${DB_USERNAME} WITH PASSWORD '${DB_PASSWORD}'" | psql
#


