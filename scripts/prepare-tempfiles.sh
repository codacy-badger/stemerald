#!/usr/bin/env bash

cd scripts
source variables.sh
cd ..

echo "
d ${TEMP_DIRECTORY} 0755 ${SERVICE_USER} ${SERVICE_USER} -
" | sudo tee /usr/lib/tmpfiles.d/${APP_NAME}.conf > /dev/null

sudo systemd-tmpfiles --create