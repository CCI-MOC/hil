#!/usr/bin/env sh
set -ex

py.test --cov=hil tests/integration/migrate_ipmi_info.py
