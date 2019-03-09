#!/bin/sh

envsubst < /etc/stemerald/config.template > ${STEMERALD_CONFIG_FILE}

while !</dev/tcp/db/5432; do sleep 1; done;

stemerald -c ${STEMERALD_CONFIG_FILE} admin create-db --basedata
stemerald -c ${STEMERALD_CONFIG_FILE} migrate upgrade head

gunicorn -w 4 --bind 0.0.0.0:8080 'wsgi:app'
