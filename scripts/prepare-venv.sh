#!/usr/bin/env bash

cd scripts
source variables.sh

PIP="python3.6 -m pip"

# Upgrading pip and setuptools
sudo ${PIP} install -U pip setuptools wheel

# Install virtualenv wrapper
sudo ${PIP} install virtualenvwrapper

# Creating the virtualenv and installing the python packages as SERVICE_USER
echo "
source \$(which virtualenvwrapper.sh);
mkvirtualenv --python=\$(which python3.6) --no-site-packages ${VIRTUALENV_NAME};
cd ..;
workon ${VIRTUALENV_NAME};
${PIP} install -e .
${PIP} install -r requirements.txt
" | sudo -EHsu ${SERVICE_USER}