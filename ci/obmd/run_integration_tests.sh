#!/usr/bin/env sh
set -ex

# The PPA version of Go stores its executables outside of the normal path, so
# we have to set this, otherwise we'll end up using Go 1.7.
export PATH="/usr/lib/go-1.10/bin:$PATH"

py.test --cov=hil --cov-append tests/integration/migrate_ipmi_info.py
