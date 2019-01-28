#!/usr/bin/env bash
export HIL_ENDPOINT=http://localhost
export HIL_USERNAME=admin
export HIL_PASSWORD=12345

# Initial Setup
cd /etc
hil-admin db create
hil-admin create-admin-user $HIL_USERNAME $HIL_PASSWORD
hil-admin serve-networks &
cd $TRAVIS_BUILD_DIR

# Test commands
py.test tests/integration/cli.py tests/integration/client_integration.py

# Test dbinit script
python examples/dbinit.py
