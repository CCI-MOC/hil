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
"""Tests for haas.rest.

This contains a somewhat awkward mix of unittest style classes and tests that
use pytest fixtures and decorators. The latter are newer,and make it workable
to use stuff like `parametrize`.
"""

from haas import rest, config

from abc import ABCMeta, abstractmethod
import unittest
import json

from schema import Schema, Optional, Use

# We don't directly use this, but unless we import it, the coverage tool
# complains and doesn't give us a report.
import pytest

from haas.test_common import config_testsuite


@pytest.fixture(autouse=True)
def configure():
    config_testsuite()
    config.load_extensions()


class HttpTest(unittest.TestCase):
    """class based version of client, for the older tests."""

    def setUp(self):
        self.client = rest.app.test_client()


@pytest.fixture()
def client():
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
        def func(foo, bar):
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
        def foo(bar, baz):
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
        def product(x, y, z=1):
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
        def some_error():
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
        def api_call():
            return None

    def test_none_return(self):
        resp = self.client.get('/nothing')
        assert resp.status_code == 200
        assert resp.get_data() == ''


@pytest.fixture()
def validation_setup():
    # There's a mix of GET, PUT and POST in these; mixing it up may give us
    # better coverage. The particulars of which PUT and POST calls get which
    # methods are arbitrary, though GET calls have some specificity.

    # We have four kinds of calls we want to validate here:

    # 1. No arguments in the URL or body (no_args)
    @rest.rest_call(['GET', 'POST'], '/no/args', Schema({}))
    def no_args():
        pass

    # 2. Argument in the URL and not in the body (url_args)
    @rest.rest_call(['GET', 'POST'], '/url/args/<arg1>/<arg2>', Schema({
        'arg1': basestring,
        'arg2': basestring,
    }))
    def url_args(arg1, arg2):
        return json.dumps([arg1, arg2])

    # 3. Arguments in both the URL and body (mixed_args)
    @rest.rest_call(['GET', 'PUT'], '/mixed/args/<arg1>', Schema({
        'arg1': basestring,
        'arg2': basestring,
    }))
    def mixed_args(arg1, arg2):
        return json.dumps([arg1, arg2])

    # 4. Arguments in body (query parameters for GET) and not in the URL.
    @rest.rest_call(['GET', 'POST'], '/just/args', Schema({
        'arg1': basestring,
        'arg2': basestring,
    }))
    def just_args(arg1, arg2):
        return json.dumps([arg1, arg2])

    # 5. One optional argument.
    @rest.rest_call(['GET', 'POST'], '/one/optional', Schema({
        'arg1': basestring,
        Optional('arg2'): Use(int),
    }))
    def one_optional(arg1, arg2=-42):
        return json.dumps([arg1, arg2])

    # Let's also make sure we're testing something with a schema that isn't
    # just basestring:
    @rest.rest_call('PUT', '/non-string-schema',
                    schema=Schema({"the_value": int}))
    def non_string_schema(the_value):
        return json.dumps(the_value)

    @rest.rest_call('GET', '/non-string-schema2',
                    schema=Schema({"the_value": Use(int)}))
    def non_string_schema2(the_value):
        return json.dumps(the_value)


def _do_request(client, method, path, data={}, query={}):
    """Make a request to the endpoint with `data` in the body.

    `client` is a flask test client

    `method` is the request method

    `path` is the path of the request

    `data` should be a string -- the server will expect valid json, but
    we want to write test cases with invalid input as well.
    """
    if method == "GET":
        return client.get(path, query_string=query, data=data)
    else:
        return client.open(method=method, path=path, data=data)


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
    # Should fail because arg is expected in URL
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
                 'path': '/just/args',
                 'query': {'arg1': 'hello',
                           'arg2': 'goodbye'}},
     'expected': {'status': 200,
                  'body_json': ['hello', 'goodbye']}},
    # Should fail because GET doesn't take body args
    {'request': {'method': 'GET',
                 'path': '/just/args',
                 'data': json.dumps({'arg1': 'hello',
                                     'arg2': 'goodbye'})},
     'expected': {'status': 400,
                  'body_json': None}},
    {'request': {'method': 'GET',
                 'path': '/just/args',
                 'query': {'arg1': '',
                           'arg2': 'goodbye'}},
     'expected': {'status': 400,
                  'body_json': None}},

    {'request': {'method': 'POST',
                 'path': '/just/args',
                 'data': json.dumps({'arg1': 'hello',
                                     'arg2': 'goodbye'})},
     'expected': {'status': 200,
                  'body_json': ['hello', 'goodbye']}},

    {'request': {'method': 'GET',
                 'path': '/one/optional',
                 'query': {'arg1': 'foo',
                           'arg2': 'bar'}},
     'expected': {'status': 400,
                  'body_json': None}},

    {'request': {'method': 'GET',
                 'path': '/one/optional',
                 'query': {'arg1': 'foo',
                           'arg2': '123'}},
     'expected': {'status': 200,
                  'body_json': ['foo', 123]}},
    {'request': {'method': 'GET',
                 'path': '/one/optional',
                 'query': {'arg1': 'foo'}},
     'expected': {'status': 200,
                  'body_json': ['foo', -42]}},

    {'request': {'method': 'GET',
                 'path': '/non-string-schema2',
                 'query': {'the_value': 42}},
     'expected': {'status': 200,
                  'body_json': 42}},
    {'request': {'method': 'PUT',
                 'path': '/non-string-schema',
                 'data': json.dumps({'the_value': 42})},
     'expected': {'status': 200,
                  'body_json': 42}},

    # Illegal JSON in the body:
    {'request': {'method': 'POST',
                 'path': '/just/args',
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
                 'path': '/just/args',
                 'data': ''},
     'expected': {'status': 400,
                  'body_json': None}},

    # Missing arg2:
    {'request': {'method': 'POST',
                 'path': '/just/args',
                 'data': json.dumps({'arg1': 'hello'})},
     'expected': {'status': 400,
                  'body_json': None}},
    # Extra arg (arg3):
    {'request': {'method': 'POST',
                 'path': '/just/args',
                 'data': json.dumps({'arg1': 'hello',
                                     'arg2': 'goodbye',
                                     'arg3': '????'})},
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
                 'path': '/non-string-schema',
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
    # Annoyingly, the client doesn't give us a way to supply an arbitrary
    # HTTP method, so we hack around it by using getattr to get the right
    # function:
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
        # We define an API call that increments a counter each time the
        # function is called, then invoke it via HTTP. Finally, we verify that
        # the counter is equal to 1, indicating that the function was called
        # the correct number of times.

        @rest.rest_call('POST', '/increment', Schema({}))
        def increment():
            """Increment a counter each time this function is called."""
            self.num_calls += 1

        self.client.post('/increment')
        assert self.num_calls == 1
