#!/usr/bin/env bash

cd scripts
source variables.sh
cd ..

SERVICE_NAME="${APP_NAME}"
SOCKET_PATH="${TEMP_DIRECTORY}/${SERVICE_NAME}.socket"

echo "
[Unit]
Description=${APP_TITLE} API service
Requires=${SERVICE_NAME}.socket
After=network.target
BindsTo=${SYSTEMD_BINDS}

[Service]
Environment="STEMERALD_CONFIG_FILE=${CONFIG_FILE}"
Environment="STEMERALD_TRUSTED_HOSTS=${TRUSTED_HOSTS}"
PIDFile=${TEMP_DIRECTORY}/${SERVICE_NAME}.pid
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=$(readlink -f .)
ExecStart=${VIRTUAL_ENV}/bin/gunicorn -w ${SERVICE_WORKERS} --bind unix:${SOCKET_PATH} --pid ${TEMP_DIRECTORY}/${SERVICE_NAME}-pid '${WSGI_APP}'
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target

" | sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null

echo "
[Unit]
Description=${APP_TITLE} unix socket

[Socket]
ListenStream=${SOCKET_PATH}

[Install]
WantedBy=sockets.target
" | sudo tee /etc/systemd/system/${SERVICE_NAME}.socket > /dev/null


echo "
upstream ${SERVICE_NAME}_backend {
    server unix:${SOCKET_PATH} fail_timeout=0;
}


server {
    listen ${SERVICE_NGINX_LISTEN};

    location / {
      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
      proxy_redirect off;
      proxy_pass http://${SERVICE_NAME}_backend;
    }
}

" | sudo tee /etc/nginx/sites-available/${SERVICE_NAME} > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.socket
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl start ${SERVICE_NAME}.service
sudo systemctl status ${SERVICE_NAME}.socket --no-pager
sudo systemctl status ${SERVICE_NAME}.service --no-pager
sudo ln -s /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/${SERVICE_NAME}
sudo service nginx reload