#!/usr/bin/env bash

#!/usr/bin/env bash

# Preparing the config file
CONFIG_FILE=~/.config/stemerald.yml
CONFIG_DIRECTORY=$(readlink -f ` dirname ${CONFIG_FILE}`)
mkdir -p ${CONFIG_DIRECTORY}

echo "
db:
  url: postgresql://postgres:postgres@localhost/stemerald_dev
  test_url: postgresql://postgres:postgres@localhost/stemerald_test
  administrative_url: postgresql://postgres:postgres@localhost/postgres
  echo: false
" > ${CONFIG_FILE}

pip3 install -U pip setuptools wheel
pip3 install --no-cache -e .
pip3 install --no-cache -r requirements.txt
pip3 install --no-cache -r requirements-dev.txt
