#!/usr/bin/env bash

# Stemerald installation script
# Version: 0.1.0
# Run the `./install-requirements.sh` at least one time before running this script.

./scripts/prepare-venv.sh
./scripts/prepare-config.sh
./scripts/prepare-db.sh
./scripts/prepare-tempfiles.sh
./scripts/install-service.sh
./scripts/install-worker-service.sh
