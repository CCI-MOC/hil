# Overview

Testing for HaaS is done using [pytest][1]. All tests
are placed in the "tests" subdirectory, which is subdivided into:

    * `unit` - for basic unit tests. These are safe to run without a
      full HaaS enviornment (i.e. you don't need libvirt etc).
    * `deployment` - for tests that need to run against an actual setup.
      Right now these aren't really generalized well enough to run
      outside of the development environment we have set up at the MOC.
      Patches welcome!

Developers should run at least the unit tests before making a commit.
Ideally, the deployment tests should also be run, though we're less
strict about this. Developers should also introduce tests for any new
functions/methods they write, or any new or fixed functionality. Ideally,
bug fixes should include a test (whether unit or functional) that reproduces
the problem scenario so that we can ensure the bug doesn't return!

# Configuration

By installing the requirements for HaaS (done via: `pip install -r
requirements.txt` in the root directory), you will automatically receive
a recent version of pytest and be ready to test the code. You also need
to have haas installed, which can be done using: `pip install -e .` from
the haas root directory. Using pip's `-e .` option installs the haas in
editable mode, which has the advantage that one need not reinstall every
time a file is changed!

Most of the tests use a common set of default configuration options, as
seen in `testsuite.cfg.default`. If you wish to override these 
parameters, you may copy it to `testsuite.cfg` and edit. In the future,
this will allow developers to do things like test against different 
DBMSes (for the moment some changes are needed to the test suite to 
actually support this).

# Running

To run all tests, from the HaaS root directory run:

    py.test tests/

To run just a subset of them, specify a particular file or directory:

    py.test tests/unit
    py.test tests/unit/api.py

As stated above, running at least `tests/unit` is mandatory before each
commit.

# Code Coverage

The pytest-cov plugin (included in requirements.txt) allows us to
generate reports indicating what code is/is not executed by our tests.
`setup.cfg` configures pytest to output coverage information by default,
so you mostly don't need to worry about this from a usage perspective --
just make sure you pay attention to the output.

More information is available on the projects [PyPI page][2].

# Test structure

Tests are kept in the `tests` directory, which is further organized into
2 subdirectories: `unit` and `deployment` \(*Not run by default*\)

For each file in the haas code, there should be a file with the same name in
the unit directory. Within those files, classes \(class names **must** begin
with "Test"\) can be used to organize tests into functional areas. Function
names must also begin with "test". See tests/unit/api.py for examples.

[1]: http://pytest.org/
[2]: https://pypi.python.org/pypi/pytest-cov
