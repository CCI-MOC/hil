#!/usr/bin/env bash

# only run pep8 on sqlite env
if [ $DB = sqlite ]; then
  cd "$(dirname $0)/.."
  pep8 $(./ci/list_tracked_pyfiles.sh)
fi
