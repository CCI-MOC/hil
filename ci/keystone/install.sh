#!/usr/bin/env sh
set -ex

pip install .[keystone-auth-backend,keystone-cli]

# The exact commit we use here is somewhat arbitrary, but we want
# something that (a) won't change out from under our feet, and (b)
# works with our existing tests.
keystone_commit=stable/pike ./ci/keystone/keystone.sh setup
