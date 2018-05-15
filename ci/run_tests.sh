#!/usr/bin/env bash

if [ $TEST_SUITE = integration ]; then
	sh -e ci/apache/run_integration_tests.sh
	sh -e ci/keystone/run_integration_tests.sh
	sh -e ci/deployment-mock-networks/run_integration_tests.sh
	sh -e ci/obmd/run_integration_tests.sh
else
	sh -e ci/pycodestyle_tests.sh
	sh -e ci/pylint_tests.sh
	sh -e ci/no_trailing_whitespace.sh
	sh -e ci/run_unit_tests.sh
fi
