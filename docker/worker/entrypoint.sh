#!/bin/sh

envsubst < /etc/stemerald/config.template > /etc/stemerald/config.yml

stemerald worker start -c /etc/stemerald/config.yml
