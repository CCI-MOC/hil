#!/usr/bin/env bash

# only run pylint on sqlite env
if [ $DB = sqlite ]; then
  cd "$(dirname $0)/.."
  pylint \
	  --disable=all \
	  --enable=unused-import \
	  $(./ci/list_tracked_pyfiles.sh)
fi
