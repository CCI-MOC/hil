#!/usr/bin/env sh
set -ex
pip install keystonemiddleware
pip install python-keystoneclient
keystone_commit=stable/mitaka ./ci/keystone/keystone.sh setup
