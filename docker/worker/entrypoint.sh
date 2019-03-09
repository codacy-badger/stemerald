#!/bin/sh



envsubst < /etc/stemerald/config.template > ${STEMERALD_CONFIG_FILE}

while !</dev/tcp/db/5432; do sleep 1; done;

stemerald worker start -c ${STEMERALD_CONFIG_FILE}
