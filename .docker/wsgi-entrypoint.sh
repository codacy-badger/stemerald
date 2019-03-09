#!/bin/sh

echo "Waiting for postgres server to be ready ..."
wait-for-it pgdb:5432 -- echo "Postgres is ready"

echo "Waiting for redis server to be ready ..."
wait-for-it redisdb:6379 -- echo "Redis is ready"

sleep 60

envsubst < /etc/stemerald/config.template.yml > ${STEMERALD_CONFIG_FILE}

stemerald -c ${STEMERALD_CONFIG_FILE} admin create-db --basedata
stemerald -c ${STEMERALD_CONFIG_FILE} migrate upgrade head

gunicorn -w 4 --bind 0.0.0.0:8080 'wsgi:app'
