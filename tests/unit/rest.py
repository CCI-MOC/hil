# Copyright 2014 Massachusetts Open Cloud Contributors (see AUTHORS).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for hil.rest.

This contains a somewhat awkward mix of unittest style classes and tests that
use pytest fixtures and decorators. The latter are newer,and make it workable
to use stuff like `parametrize`.
"""

# Note regarding pylint: in this module, we define a number of methods that
# are only called implicitly via the HTTP/flask machinery. As such, pylint
# will erroneously flag them as unused variables -- we disable that warning
# locally in many places in this module.

from hil import rest, config

from abc import ABCMeta, abstractmethod
import unittest
import json
import logging

from schema import Schema, Optional, Use
import pytest

from hil.test_common import config_testsuite, fail_on_log_warnings

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)


# This will get pulled in automaticaly, but if we declare it we'll get
# better error messages if something goes wrong:
pytest_plugins = 'pytest_catchlog'


@pytest.fixture(autouse=True)
def configure():
    """Set up the HIL config."""
    config_testsuite()
    config.configure_logging()
    config.load_extensions()


class HttpTest(unittest.TestCase):
    """class based version of client, for the older tests."""

    def setUp(self):
        self.client = rest.app.test_client()


@pytest.fixture()
def client():
    """ Creates a test client based on FlaskClient, which is underpinned by
    werkzeug.test.Client(), documented at:
    http://werkzeug.pocoo.org/docs/0.11/test/#werkzeug.test.Client
    """
    return rest.app.test_client()


class HttpEquivalenceTest(object):
    """A test that ensures a particlar call to the api behaves the same over
    http and when called as a function. Subclasses must override `api_call`
    and `request`, and may also be interested in `api_setup` and
    `api_teardown`.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def api_call(self):
        """Invoke the api call directly."""

    @abstractmethod
    def request(self):
        """Invoke the API cal via HTTP. returning the response.

        When this method is invoked, `self.client` will be an instance of
        `flask.testing.FlaskClient`, and should be used to make the request.
        Its return value is the response, and should be returned as-is.
        """

    def api_setup(self):
        """Setup routine to be run before each call to the api.

        This is conceptually similar to python's unittest setUp()
        method, but with each call to `api_call`, rather than the
        whole test.

        By default this is a noop; subclasses should override this if
        they need specific environments.
        """

    def api_teardown(self):
        """like `api_setup`, but tears things down after the call."""

    def test_equivalence(self):
        """Calling `api_call` directly should be the same as via http."""

        # First invoke the call over http. This should never raise exceptions.
        self.api_setup()
        resp = self.request()
        body = resp.get_data()
        self.api_teardown()

        # Now call it directly.
        try:
            self.api_setup()
            ret = self.api_call()

            # Flask has a few different things a function can return; we need
            # to handle each of them.
            if ret is None:
                ret_body, ret_status = '', 200
            elif type(ret) is tuple:
                ret_body, ret_status = ret
            else:
                ret_body, ret_status = ret, 200

            assert resp.status_code == ret_status
            if ret_body == '':
                assert body == ''
            else:
                assert json.loads(body) == json.loads(ret_body)
        except rest.APIError as e:
            assert resp.status_code == e.status_code
            assert json.loads(body) == {'type': e.__class__.__name__,
                                        'msg': e.message,
                                        }
        finally:
            self.api_teardown()


class TestUrlArgs(HttpEquivalenceTest, HttpTest):
    """Test that arguments supplied in the url are passed correctly."""
    # The use of HTTPEquivalenceTest here is a bit weird; We're not actually
    # calling the api function from `api_call`. This is actually probably a
    # fairly common way to want to use the superclass; we should think about
    # whether the documented usage is necessarily the right idea.

    def setUp(self):
        HttpTest.setUp(self)

        @rest.rest_call('GET', '/func/<foo>/<bar>', Schema({
            'foo': basestring,
            'bar': basestring,
        }))
        # pylint: disable=unused-variable
        def func(foo, bar):
            """Return URL arguments as a JSON list."""
            return json.dumps([foo, bar])

    def api_call(self):
        return json.dumps(['alice', 'bob'])

    def request(self):
        return self.client.get('/func/alice/bob')


class TestBodyArgs(HttpEquivalenceTest, HttpTest):
    """Test that arguments supplied in the body are passed correctly."""

    def setUp(self):
        HttpTest.setUp(self)

        @rest.rest_call('POST', '/func/foo', Schema({
            'bar': basestring,
            'baz': basestring,
        }))
        # pylint: disable=unused-variable
        def foo(bar, baz):
            """Return body arguments as a JSON list."""
            return json.dumps([bar, baz])

    def api_call(self):
        return json.dumps(['bonnie', 'clyde'])

    def request(self):
        return self.client.post('/func/foo',
                                data=json.dumps({'bar': 'bonnie',
                                                 'baz': 'clyde'}))


class TestRestCallSchema(HttpEquivalenceTest, HttpTest):
    """Test using non-trivial schema (i.e. not just strings)."""

    def setUp(self):
        HttpTest.setUp(self)

        @rest.rest_call('POST', '/product', schema=Schema({
            'x': int,
            'y': int,
            Optional('z'): int,
        }))
        # pylint: disable=unused-variable
        def product(x, y, z=1):
            """Multiply arguments from the body."""
            return json.dumps(x * y * z)

    def api_call(self):
        return json.dumps(14)

    def request(self):
        return self.client.post('/product',
                                data=json.dumps({'x': 2, 'y': 7}))


class TestEquiv_basic_APIError(HttpEquivalenceTest, HttpTest):
    """Basic test to make sure the APIError handling code is excercised."""

    def setUp(self):
        HttpTest.setUp(self)

        @rest.rest_call('GET', '/some_error', Schema({}))
        # pylint: disable=unused-variable
        def some_error():
            """Raise an APIError."""
            self.api_call()

    def api_call(self):
        raise rest.APIError("Basic test of the APIError code.")

    def request(self):
        return self.client.get('/some_error')


class TestNoneReturnValue(HttpTest):
    """Test returning None from API calls.

    Flask itself doesn't allow this, but we've been doing it for a long time
    so our wrapper supports it. This test verifies that it actually works.
    """

    def setUp(self):
        HttpTest.setUp(self)

        @rest.rest_call('GET', '/nothing', Schema({}))
        # pylint: disable=unused-variable
        def api_call():
            """Return None"""
            return None

    def test_none_return(self):
        """Returning None should return 200 OK with an empty body."""
        resp = self.client.get('/nothing')
        assert resp.status_code == 200
        assert resp.get_data() == ''


@pytest.fixture()
def validation_setup():
    """Fixture registering of api calls with a variety of arguments/results."""
    # There's a mix of GET, PUT and POST in these; mixing it up may give us
    # better coverage. The particulars of which PUT and POST calls get which
    # methods are arbitrary, though GET calls have some specificity.

    # We have several kinds of calls we want to validate here:

    @rest.rest_call(['GET', 'POST'], '/no/args', Schema({}))
    # pylint: disable=unused-variable
    def no_args():
        """Call with no arguments in the URL or body"""

    @rest.rest_call(['GET', 'POST'], '/url/args/<arg1>/<arg2>', Schema({
        'arg1': basestring,
        'arg2': basestring,
    }))
    # pylint: disable=unused-variable
    def url_args(arg1, arg2):
        """Call with arguments in the URL and not in the body"""
        return json.dumps([arg1, arg2])

    @rest.rest_call(['GET', 'PUT'], '/mixed/args/<arg1>', Schema({
        'arg1': basestring,
        'arg2': basestring,
    }))
    # pylint: disable=unused-variable
    def mixed_args(arg1, arg2):
        """Call with arguments in both the URL and body"""
        return json.dumps([arg1, arg2])

    @rest.rest_call(['GET', 'POST'], '/just/bodyargs', Schema({
        'arg1': basestring,
        'arg2': basestring,
    }))
    # pylint: disable=unused-variable
    def just_bodyargs(arg1, arg2):
        """
        Call with arguments in body (query params for GET) and not in the URL.
        """
        return json.dumps([arg1, arg2])

    @rest.rest_call(['GET', 'POST'], '/just/bodyargs/optional_arg2_int',
                    Schema({'arg1': basestring,
                            Optional('arg2'): Use(int),
                            }))
    # pylint: disable=unused-variable
    def bodyargs_optional_arg2_int(arg1, arg2=-42):
        """One optional argument"""
        return json.dumps([arg1, arg2])

    # Let's also make sure we're testing something with a schema that isn't
    # just basestring:
    @rest.rest_call('PUT', '/put-int-body-arg',
                    schema=Schema({"the_value": int}))
    # pylint: disable=unused-variable
    def put_int_body_arg(the_value):
        """Call with an argument that's not a basestring (int)"""
        return json.dumps(the_value)

    @rest.rest_call('GET', '/get-int-body-arg-with-use',
                    schema=Schema({"the_value": Use(int)}))
    # pylint: disable=unused-variable
    def get_int_body_arg_with_use(the_value):
        """Call with Use in the schema

        This makes sure that rest_call is correctly passing us the result of
        validation, rather than the original input.
        """
        return json.dumps(the_value)


def _do_request(client, method, path, data=None, query=None):
    """Make a request to the endpoint with `data` in the body.

    `client` is a flask test client

    `method` is the request method

    `path` is the path of the request

    `data` a dictionary containing body arguments for non-GET methods that will
    be converted to JSON -- the server will expect valid json, but we want to
    write test cases with invalid input as well.

    `query` a dictionary containing query arguments (ie - those after the ?)
    for the GET method.

    """

    # The arguments for this method are documented at:
    # http://werkzeug.pocoo.org/docs/0.11/test/#werkzeug.test.EnvironBuilder
    return client.open(method=method, path=path, query_string=query, data=data)


@pytest.mark.parametrize('args', [
    {'request': {'method': 'GET', 'path': '/no/args'},
     'expected': {'status': 200, 'body_json': None}},
    {'request': {'method': 'POST', 'path': '/no/args', 'data': ''},
     'expected': {'status': 200, 'body_json': None}},

    {'request': {'method': 'POST',
                 'path': '/url/args/hello/goodbye',
                 'data': ''},
     'expected': {'status': 200,
                  'body_json': ['hello', 'goodbye']}},
    {'request': {'method': 'GET',
                 'path': '/url/args/hello/goodbye'
                 },
     'expected': {'status': 200,
                  'body_json': ['hello', 'goodbye']}},

    # Should fail because arg2 is expected in URL
    {'request': {'method': 'GET',
                 'path': '/url/args/hello/',
                 'query': {'arg2': "goodbye"}
                 },
     'expected': {'status': 404,
                  'body_json': None}},

    {'request': {'method': 'PUT',
                 'path': '/mixed/args/hello',
                 'data': json.dumps({'arg2': 'goodbye'})},
     'expected': {'status': 200,
                  'body_json': ['hello', 'goodbye']}},
    {'request': {'method': 'GET',
                 'path': '/mixed/args/hello',
                 'query': {'arg2': 'goodbye'}},
     'expected': {'status': 200,
                  'body_json': ['hello', 'goodbye']}},
    # Should fail because GET doesn't take body args
    {'request': {'method': 'GET',
                 'path': '/mixed/args/hello',
                 'query': {'arg2': 'goodbye'},
                 'data': json.dumps({'arg2': 'goodbye'})},
     'expected': {'status': 400,
                  'body_json': None}},
    {'request': {'method': 'GET',
                 'path': '/mixed/args/hello',
                 'data': json.dumps({'arg2': 'goodbye'})},
     'expected': {'status': 400,
                  'body_json': None}},

    {'request': {'method': 'GET',
                 'path': '/just/bodyargs',
                 'query': {'arg1': 'hello',
                           'arg2': 'goodbye'}},
     'expected': {'status': 200,
                  'body_json': ['hello', 'goodbye']}},
    # Should fail because GET doesn't take body args
    {'request': {'method': 'GET',
                 'path': '/just/bodyargs',
                 'data': json.dumps({'arg1': 'hello',
                                     'arg2': 'goodbye'})},
     'expected': {'status': 400,
                  'body_json': None}},
    {'request': {'method': 'GET',
                 'path': '/just/bodyargs',
                 'query': {'arg1': '',
                           'arg2': 'goodbye'}},
     'expected': {'status': 400,
                  'body_json': None}},

    {'request': {'method': 'POST',
                 'path': '/just/bodyargs',
                 'data': json.dumps({'arg1': 'hello',
                                     'arg2': 'goodbye'})},
     'expected': {'status': 200,
                  'body_json': ['hello', 'goodbye']}},

    # Missing arg2:
    {'request': {'method': 'POST',
                 'path': '/just/bodyargs',
                 'data': json.dumps({'arg1': 'hello'})},
     'expected': {'status': 400,
                  'body_json': None}},
    # Extra arg (arg3):
    {'request': {'method': 'POST',
                 'path': '/just/bodyargs',
                 'data': json.dumps({'arg1': 'hello',
                                     'arg2': 'goodbye',
                                     'arg3': '????'})},
     'expected': {'status': 400,
                  'body_json': None}},


    {'request': {'method': 'GET',
                 'path': '/just/bodyargs/optional_arg2_int',
                 'query': {'arg1': 'foo',
                           'arg2': 'bar'}},
     'expected': {'status': 400,
                  'body_json': None}},

    {'request': {'method': 'GET',
                 'path': '/just/bodyargs/optional_arg2_int',
                 'query': {'arg1': 'foo',
                           'arg2': '123'}},
     'expected': {'status': 200,
                  'body_json': ['foo', 123]}},
    {'request': {'method': 'GET',
                 'path': '/just/bodyargs/optional_arg2_int',
                 'query': {'arg1': 'foo'}},
     'expected': {'status': 200,
                  'body_json': ['foo', -42]}},

    {'request': {'method': 'GET',
                 'path': '/get-int-body-arg-with-use',
                 'query': {'the_value': 42}},
     'expected': {'status': 200,
                  'body_json': 42}},
    {'request': {'method': 'GET',
                 'path': '/get-int-body-arg-with-use',
                 'query': {'the_value': "42"}},
     'expected': {'status': 200,
                  'body_json': 42}},

    # These should fail: passing a float, and then a totally invalid value.
    {'request': {'method': 'GET',
                 'path': '/get-int-body-arg-with-use',
                 'query': {'the_value': 42.234}},
     'expected': {'status': 400,
                  'body_json': None}},
    {'request': {'method': 'GET',
                 'path': '/get-int-body-arg-with-use',
                 'query': {'the_value': "42.A"}},
     'expected': {'status': 400,
                  'body_json': None}},

    {'request': {'method': 'PUT',
                 'path': '/put-int-body-arg',
                 'data': json.dumps({'the_value': 42})},
     'expected': {'status': 200,
                  'body_json': 42}},

    # Illegal JSON in the body:
    {'request': {'method': 'POST',
                 'path': '/just/bodyargs',
                 'data': 'xploit'},
     'expected': {'status': 400,
                  'body_json': None}},

    # Arguments in the body for a function that expects no arguments
    {'request': {'method': 'POST', 'path': '/no/args',
                 'data': json.dumps({'arg1': 'foo'})},
     'expected': {'status': 400, 'body_json': None}},
    {'request': {'method': 'GET', 'path': '/no/args',
                 'data': json.dumps({'arg1': 'foo'})},
     'expected': {'status': 400, 'body_json': None}},

    # Empty body (for a function that expects body args). Note that this should
    # hit the same exact code paths as the illegal JSON test, but it's
    # conceptually different:
    {'request': {'method': 'POST',
                 'path': '/just/bodyargs',
                 'data': ''},
     'expected': {'status': 400,
                  'body_json': None}},
    # Same argument passed via URL and body. Note that from the client side
    # this isn't semantically meaningful, since arguments in the URL don't have
    # names; this is just testing the logic that parses these into python
    # function arguments:
    {'request': {'method': 'PUT',
                 # The mixed_args function calls the 'hello' segment of it's
                 # path "arg1":
                 'path': '/mixed/args/hello',
                 'data': json.dumps({'arg1': 'howdy',
                                     'arg2': 'goodbye'})},
     'expected': {'status': 400,
                  'body_json': None}},

    # Invalid arg types:
    {'request': {'method': 'PUT',
                 'path': '/mixed/args/hello',
                 'data': json.dumps({'arg2': 3232})},
     'expected': {'status': 400,
                  'body_json': None}},

    {'request': {'method': 'PUT',
                 'path': '/put-int-body-arg',
                 'data': json.dumps({'the_value': 'Not an integer!'})},
     'expected': {'status': 400, 'body_json': None}},

])
def test_validation_status(client, validation_setup, args):
    """Check that the request returns an expected response.

    `client` and `validation_setup` come from the fixtures defined above.

    `args` is a dictionary with two keys:

        * `request`, a specification of the request
        * `expected` a specification of the expected response.

    `request` has three fields, `method`, `path`, and `data`, corresponding
    to the arguments to `_do_request` by the same names.

    `expected` has two fields:

        * `status`, the expected status code.
        * `body_json`, which is either a decoded JSON object or `None`.
           If it is None, no requirements are imposed on the body of the
           request. Otherwise, it must be equal to the decoded body of the
           response.

    """
    resp = _do_request(client, **args['request'])
    assert resp.status_code == args['expected']['status'],\
        (args, resp.get_data())

    if args['expected']['body_json'] is not None:
        assert json.loads(resp.get_data()) == args['expected']['body_json'],\
               (args, resp.get_data())


class TestCallOnce(HttpTest):
    """Verify that the request handler invokes the API *exactly* once.

    This is a regression test; A previous refactoring introduced a bug where
    the api function was called twice.
    """

    def setUp(self):
        HttpTest.setUp(self)
        self.num_calls = 0

    def test_call_once(self):
        """Verify that we only call an API function once per request."""
        # We define an API call that increments a counter each time the
        # function is called, then invoke it via HTTP. Finally, we verify that
        # the counter is equal to 1, indicating that the function was called
        # the correct number of times.

        @rest.rest_call('POST', '/increment', Schema({}))
        # pylint: disable=unused-variable
        def increment():
            """Increment a counter each time this function is called."""
            self.num_calls += 1

        self.client.post('/increment')
        assert self.num_calls == 1


def test_dont_log(client, caplog):
    """Test the ``dont_log`` argument to rest_call."""

    @rest.rest_call('POST', '/some-path', Schema({
        'public': basestring,
        'private': basestring,
        'stuff': basestring,
    }), dont_log=('private',))
    # pylint: disable=unused-variable
    def some_call(public, private, stuff):
        """API Call that doesn't do anything.

        This is here just so we have an API call to test with, but all of
        the logic we're testing is in the common hil.rest machinery, so it
        doesn't actually need to do anything.
        """

    with caplog.at_level(logging.DEBUG):
        resp = client.post('/some-path', data=json.dumps({
            'public': 'common knowledge',
            'private': 'sensitive info',
            'stuff': 'Other stuff',
        }))
        assert resp.status_code == 200, \
            "An error occured handling the request!"
        for record in caplog.records():
            assert 'sensitive info' not in record.getMessage()
