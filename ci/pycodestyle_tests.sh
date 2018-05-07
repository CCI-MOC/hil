#!/usr/bin/env bash

# If we're running in CI, only run pycodestyle in the sqlite env.
# If the DB variable is undefined we assume a developer has invoked
# this script directly.
if [ -z "$DB" ] || [ "$DB" = sqlite ]; then
  cd "$(dirname $0)/.."
  pycodestyle $(./ci/list_tracked_pyfiles.sh)
fi
