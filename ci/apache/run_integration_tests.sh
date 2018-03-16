#!/usr/bin/env bash
export HIL_ENDPOINT=http://localhost
export HIL_USERNAME=admin
export HIL_PASSWORD=12345

# Initial Setup
cd /etc
hil-admin db create
hil-admin create_admin_user $HIL_USERNAME $HIL_PASSWORD
cd $TRAVIS_BUILD_DIR

# Test commands
py.test --cov=hil --cov-append tests/integration/cli.py

# Test dbinit script
python examples/dbinit.py
