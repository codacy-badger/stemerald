#!/bin/sh

envsubst < /etc/stemerald/config.template > /etc/stemerald/config.yml
gunicorn -w 4 --bind 0.0.0.0:8080 'wsgi:app'
