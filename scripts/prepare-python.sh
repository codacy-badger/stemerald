#!/usr/bin/env bash

# Installing Python3.6.4
R=$(pwd)
cd /tmp
curl https://www.python.org/ftp/python/3.6.4/Python-3.6.4.tgz | tar -xzf -
cd Python-3.6.4
./configure
make
sudo make altinstall
cd ..
sudo rm -r Python-3.6.4
cd ${R}

echo "Python-3.6.4 installed successfully!"#!/usr/bin/env bash