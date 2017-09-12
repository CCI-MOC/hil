#!/usr/bin/env bash

# If we're running in CI, only run pylint in the sqlite env.
# If the DB variable is undefined we assume a developer has
# invoked this script directly.
if [ -z "$DB" ] || [ "$DB" = sqlite ]; then
  cd "$(dirname $0)/.."
  pylint \
	  --disable=all \
	  --enable=undefined-variable \
	  --enable=unused-variable \
	  --enable=unused-import \
	  --enable=wildcard-import \
	  --enable=signature-differs \
	  --enable=arguments-differ \
	  --enable=missing-docstring \
	  --enable=logging-not-lazy \
	  --enable=reimported \
	  $(./ci/list_tracked_pyfiles.sh)
fi
