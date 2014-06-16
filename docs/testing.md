# Overview

Testing for HaaS is done using [pytest](http://pytest.org/). All tests
are placed in the "tests" subdirectory, which has 3 directories: unit,
functional and integration.

Unit tests focus on testing indvidual functions. For example, testing
user_create() would entail a test that creates a user and perhaps trying
to create a user twice. Unit tests might also include other function calls
as well if they are necessary. Testing user_delete() might first require
calling user_create().

Functional tests verify higher levels of functionality and integration. This
might include calling not only user_create() and user_delete(), but also
changing the password, adding a user to a group, and so forth. The intention
is to ensure particular user stories function as they are supposed to,
and ensure that scenarios which shouldn't happen don't.

Integration tests exercise the entire stack, from the highest level API to
the lowest level driver. These tests will likely require physical switch
hardware (or a mock switch driver) to run, and thus won't run by default.

It is intended (and the default configuration) to run unit and functional
tests before any commit. Developers should also introduce unit tests for any
new functions/methods they write, or any new or fixed functionality. Ideally,
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

# Running

To run all tests, from the HaaS root directory run:

    py.test tests/

To run just a subset of them, specify a particular file or directory:

    py.test tests/unit
    py.test tests/unit/api.py

# Test structure

Tests are kept in the `tests` directory, which is further organized into
3 subdirectories: * unit * functional * integration \(*Not run by default*\)

For each file in the haas code, there should be a file with the same name in
the unit directory. Within those files, classes \(class names **must** begin
with "Test"\) can be used to organize tests into functional areas. Function
names must also begin with "test". See tests/unit/api.py for examples.
