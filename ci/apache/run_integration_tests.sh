#!/usr/bin/env bash
export HIL_ENDPOINT=http://localhost
export HIL_USERNAME=admin
export HIL_PASSWORD=12345

# Initial Setup
cd /etc
hil-admin db create
hil-admin create-admin-user $HIL_USERNAME $HIL_PASSWORD
cd $TRAVIS_BUILD_DIR

# Test commands
py.test --cov=hil --cov-append tests/integration/cli.py
py.test --cov=hil --cov-append tests/integration/client.py

# Test dbinit script
python examples/dbinit.py
