#!/usr/bin/env bash

# only run pycodestyle on sqlite env
if [ $DB = sqlite ]; then
  cd "$(dirname $0)/.."
  pycodestyle $(./ci/list_tracked_pyfiles.sh)
fi
