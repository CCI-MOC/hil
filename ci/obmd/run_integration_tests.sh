#!/usr/bin/env sh
set -ex

py.test tests/integration/migrate_ipmi_info.py
