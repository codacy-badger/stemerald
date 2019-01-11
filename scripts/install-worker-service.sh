#!/usr/bin/env bash

cd scripts
source variables.sh
cd ..


SERVICE_NAME="${APP_NAME}-worker"

echo "
[Unit]
Description=${APP_TITLE} worker daemon
After=network.target
BindsTo=${SYSTEMD_BINDS}

[Service]
Environment="EMERALD_CONFIG_FILE=${CONFIG_FILE}"
PIDFile=${TEMP_DIRECTORY}/${SERVICE_NAME}.pid
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=$(readlink -f .)
ExecStartPre=${EMERALD} worker cleanup
ExecStart=${EMERALD} worker start
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl start ${SERVICE_NAME}.service
sudo systemctl status ${SERVICE_NAME}.service --no-pager
