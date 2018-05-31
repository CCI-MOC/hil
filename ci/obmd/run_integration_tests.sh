#!/usr/bin/env sh
set -ex

py.test --cov=hil --cov-append tests/integration/obmd.py
