#!/bin/sh

envsubst < /etc/stemerald/config.template > ${STEMERALD_CONFIG_FILE}
stemerald -c ${STEMERALD_CONFIG_FILE} admin create-db --basedata
stemerald -c ${STEMERALD_CONFIG_FILE} migrate upgrade head

gunicorn -w 4 --bind 0.0.0.0:8080 'wsgi:app'
