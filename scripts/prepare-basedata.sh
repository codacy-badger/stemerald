#!/usr/bin/env bash

cd scripts
source variables.sh

echo "
source variables.sh;
source \$(which virtualenvwrapper.sh);
workon ${VIRTUALENV_NAME};
${STEMERALD} admin base-data
" | sudo -EHsu ${SERVICE_USER}