#!/bin/sh

envsubst < /etc/stemerald/config.template > ${STEMERALD_CONFIG_FILE}

stemerald worker start -c ${STEMERALD_CONFIG_FILE}
