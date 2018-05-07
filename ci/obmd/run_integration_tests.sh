#!/usr/bin/env sh
set -ex

# Set environment variables so we use the newer version of Go, rather than
# the 1.7 that's installed in Travis by default:
export GOROOT=/usr/lib/go-1.10
export PATH="$HOME/go/bin:/usr/lib/go-1.10/bin:$PATH"

# Just in case, forget any cached command locations:
hash -r

go get -v github.com/CCI-MOC/obmd

py.test --cov=hil --cov-append tests/integration/obmd.py
