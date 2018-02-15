#!/usr/bin/env sh

set -ex

./ci/keystone/keystone.sh run &

# Wait for curl to successfully connect to each of the ports keystone
# is supposed to be listening on before continuing.
for port in 5000 35357; do
	while [ "$(curl http://127.0.0.1:$port; echo $?)" -ne 0 ]; do
		sleep .2
	done
done

py.test --cov=hil tests/integration/keystone.py
