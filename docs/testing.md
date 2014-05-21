# Testing

We're using [nose][1] for testing. Our tests are in `haas/_tests`,
typically with a filename that matches the module they are testing (so
for example tests for `haas.cli` go in `haas/_tests/cli.py`).

Extra packages needed only for testing go in a separate requirements
file, `test-requirements.txt`. To install them, execute:

    pip install -r test-requirements.txt

To run all of the tests, execute:

    nosetests haas/_tests/*.py
