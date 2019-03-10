#!/bin/bash

echo ${STEMERALD_CONFIG_FILE}
echo ${STEMERALD_CONFIG_FILE}
echo ${STEMERALD_CONFIG_FILE}
echo ${STEMERALD_CONFIG_FILE}
echo ${STEMERALD_CONFIG_FILE}
echo ${STEMERALD_CONFIG_FILE}
echo ${STEMERALD_CONFIG_FILE}
echo ${STEMERALD_CONFIG_FILE}
echo ${STEMERALD_CONFIG_FILE}

help () {
	echo "Available daemons are: "
	echo "  wsgi"
	echo "  worker"
	echo "  cli"
}

echo "@=$@"

if [ $# -lt 1 ];then
	help
	exit 0
fi

SERVICE=$1

initconfig () {
    envsubst < /etc/stemerald/config.template.yml > ${STEMERALD_CONFIG_FILE}
}
waitfordeps () {
    echo "Waiting for postgres server to be ready ..."
    wait-for-it pgdb:5432 -- echo "Postgres is ready"

    echo "Waiting for redis server to be ready ..."
    wait-for-it redisdb:6379 -- echo "Redis is ready"
}

case $SERVICE in
	cli)
	    initconfig
	    waitfordeps
        tail -f /dev/null
		;;
	worker)
		initconfig
		waitfordeps
        stemerald -c ${STEMERALD_CONFIG_FILE} worker start
		;;
	wsgi)
		initconfig
		waitfordeps
        stemerald -c ${STEMERALD_CONFIG_FILE} admin setup-db
        stemerald -c ${STEMERALD_CONFIG_FILE} migrate upgrade head
        stemerald -c ${STEMERALD_CONFIG_FILE} admin base-data
        gunicorn -w 4 --bind 0.0.0.0:8080 'wsgi:app'
		;;
	--help)
		help
		;;
	-h)
		help
		;;
  *)
		exec $@
		;;
esac

if [ $BASH ]; then
	while true;do sleep 3600;done
else
	exit 101
fi
