# Testing

## Overview

Testing for HIL is done using [pytest][1]. All tests
are placed in the "tests" subdirectory, which is subdivided into:

* `unit` - for basic unit tests. These are safe to run without a full HIL enviornment (i.e. you don't need libvirt etc).
* `deployment` - for tests that need to run against an actual setup, with libvirtd and at least one real switch.

Developers should run at least the unit and pep8 tests before making a commit.
Ideally, the deployment tests should also be run, though we're less
strict about this. Developers should also introduce tests for any new
functions/methods they write, or any new or fixed functionality. Ideally,
bug fixes should include a test (whether unit or functional) that reproduces
the problem scenario so that we can ensure the bug doesn't return!

## Configuration

Install HIL and its test dependencies in the virtual environment, done
via: `pip install -e .[tests]` in the root directory. This will pull
a recent version of pytest and you'll be ready to test the code. Using
pip's `-e` option installs the hil in editable mode, which has the
advantage that one need not reinstall every time a file is changed!

Most of the tests use a common set of default configuration options, as
seen in `testsuite.cfg.default`. If you wish to override these
parameters, you may copy it to `testsuite.cfg` and edit. In the future,
this will allow developers to do things like test against different
DBMSes (for the moment some changes are needed to the test suite to
actually support this). For now, it's mostly interesting when running
the deployment tests (see below).

## Running

To run all tests, from the HIL root directory run:

    py.test tests/

To run just a subset of them, specify a particular file or directory:

    py.test tests/unit
    py.test tests/unit/api.py

To run just a pep8 test:

    pep8 *.py tests/ hil/

As stated above, running at least `tests/unit` is mandatory before each
commit.

## Code Coverage

The pytest-cov plugin (included in requirements.txt) allows us to
generate reports indicating what code is/is not executed by our tests.
`setup.cfg` configures pytest to output coverage information by default,
so you mostly don't need to worry about this from a usage perspective --
just make sure you pay attention to the output.

More information is available on the projects [PyPI page][2].

## Test structure

Tests are kept in the `tests` directory, which is further organized into
a few subdirectories:

* `unit`
* `integration`
* `deployment`

For each file in the hil code, there should be a file with the same name in
the unit directory. Within those files, classes (class names **must**
begin with "Test") can be used to organize tests into functional areas.
Function names must also begin with "test". See tests/unit/api.py for
examples.

There also may be a few files loose in the `tests` directory that do not
clearly fit into one of the above categories.

## Integration tests

The `tests/integration` directory contains tests that require
substantial setup of external software, or special configuration. These
tend to be expensive in terms of time. These are run automatically by
our travis-ci configuration.

## Deployment tests

The deployment tests (`tests/deployment`) are a set of unit tests which
are most useful when executed in an environment with real hardware and a
libvirtd instance available. Some of these are executed by our travis-ci
configuration using mock drivers, but (obviously) not against real
hardware. They should be run before merging any patch relating to
specific hardware support, or interacting with headnodes. To run the
deployment tests, you must do the following:

* Write a `testsuite.cfg` reflecting your environment. Copy
  `examples/testsuite.cfg-deployment` and edit. In particular, you will
  need to load the extensions for your switch drivers and the
  corresponding network allocator (see `drivers.md`), and specify
  extension-specific options.
* Write a `site-layout.json` describing the layout of your environment.
  The file `examples/site-layout.json` provides an example. Here is a
  full description of the file format:

`site-layout.json` must contain a single json object, with two fields:
`"switches"` and `"nodes"`.

`"switches"` must be a list of json objects, each of which describes a
switch in your environment, and must have the same fields as required in
the body of  the `switch_register` API call (see `rest_api.md`), plus a
`"switch"` field, which supplies the name of the switch (normally
specified in the URL).

`"nodes"` must be a list of json objects, each of which defines a node,
and has three fields:

* `"name"`, a string which specifies the name of the node.
* `"nics"`, a list of objects each describing a nic on the node, with the
  fields (all of them strings):
  * `"name"`, the name of the nic
  * `"mac"`, the mac address of the nic
  * `"switch"`, the name of the switch that the nic is connected to
  * `"port"`, the name/label of the port on the switch that the nic is
    connected to
* `"obm"`, An object with the same set of fields as required by the obm
  field in the `node_register` API call.

The tests currently require at least four nodes to be specified in
`site-layout.json`, each of which must have at least one nic connected
to the switch.

[1]: http://pytest.org/
[2]: https://pypi.python.org/pypi/pytest-cov
