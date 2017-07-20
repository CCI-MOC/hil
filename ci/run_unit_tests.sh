#!/usr/bin/env bash

# On SQLite we run the tests in parallel.
# This speeds things up, but is currently only safe for sqlite, since it uses
# an in memory (and  therefore per-process) database.

if [ $DB = sqlite ]; then
    extra_flags='-n auto'
fi

py.test $extra_flags \
	tests/custom_lint.py \
	tests/unit \
	tests/stress.py
