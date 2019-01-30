#!/usr/bin/env bash

#Installing locales
sudo locale-gen en_US.UTF-8 fa_IR.UTF-8

# Updating indexes
sudo apt-get update

# Upgrading the system
sudo apt-get dist-upgrade -y

# Installing dependencies
sudo apt-get install -y locales nano net-tools curl build-essential make libpq-dev git wget zlib1g-dev libbz2-dev \
     libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev ssh openssh-server \
     apt-utils python-software-properties software-properties-common redis-server nginx postgresql libmagickwand-dev

# Uncomment this on docker:
## Add ppa's
#sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8
#echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" \
#     | sudo tee /etc/apt/sources.list.d/pgdg.list > /dev/null
#sudo apt-get install -y postgresql-9.3 postgresql-client-9.3 postgresql-contrib-9.3

echo "Apt prepared successfully!"
