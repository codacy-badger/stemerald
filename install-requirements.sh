#!/usr/bin/env bash

# Stacrypt requirement installation script
# Version: 0.1.0
# Please configure apt sources, locales, networking and etc first.

./scripts/prepare-apt.sh
./scripts/prepare-python.sh

echo "Done, please reboot your box, then you can install this app."
