#!/usr/bin/env sh
set -ex
pip install keystonemiddleware
pip install python-keystoneclient
./ci/keystone/keystone.sh setup
