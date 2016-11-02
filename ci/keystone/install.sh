#!/usr/bin/env sh
set -ex
pip install keystonemiddleware
pip install python-keystoneclient
# The exact commit we use here is somewhat arbitrary, but we want
# something that (a) won't change out from under our feet, and (b)
# works with our existing tests.
keystone_commit=10.0.0.0rc3 ./ci/keystone/keystone.sh setup
