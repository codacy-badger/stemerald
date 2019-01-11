#!/usr/bin/env bash

cd scripts
source variables.sh

CONFIG_DIRECTORY=$(readlink -f ` dirname ${CONFIG_FILE}`)
sudo mkdir -p ${CONFIG_DIRECTORY}


cat config.yml | sudo tee ${CONFIG_FILE} > /dev/null

sudo mkdir -p ${LOG_DIR}
sudo chown ${SERVICE_USER}:${SERVICE_USER} ${LOG_DIR}