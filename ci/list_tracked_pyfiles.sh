#!/usr/bin/env bash
# This script lists all of the python source files that are tracked
# by git. The primary use is deciding what files to run the linters on.

set -e

cd "$(git rev-parse --show-toplevel)" # Enter the source tree root

# List all files not matched by a .gitignore and ending in .py or .wsgi.
git ls-files $(find -name .gitignore | sed 's/^/--exclude-per-directory /') | \
	grep -E '\.(py|wsgi)$'
