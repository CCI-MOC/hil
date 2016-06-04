#!/usr/bin/env bash
export HAAS_ENDPOINT=http://localhost
export HAAS_USERNAME=admin
export HAAS_PASSWORD=12345

# Initial Setup
# source env/bin/activate
cd /etc
haas-admin db create
haas create_admin_user $HAAS_USERNAME $HAAS_PASSWORD
cd $TRAVIS_BUILD_DIR

# Test commands
py.test tests/integration/cli.py
