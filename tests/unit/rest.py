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
from haas import rest, config

from abc import ABCMeta, abstractmethod
import unittest
import json

from schema import Schema, Optional

# We don't directly use this, but unless we import it, the coverage tool
# complains and doesn't give us a report.
import pytest

from haas.test_common import config_testsuite


@pytest.fixture(autouse=True)
def configure():
    config_testsuite()
    config.load_extensions()


class HttpTest(unittest.TestCase):

    def setUp(self):
        self.client = rest.app.test_client()


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


def _is_error(resp, errtype):
    """Return True iff the Response `resp` represents an `errtype`.

    `resp` should be a response returned by `request_handler`.
    `errtype` should be a subclass of APIError.
    """
    try:
        return json.loads(resp.get_data())['type'] == errtype.__name__
    except:
        # It's possible that this response isn't even an error, in which case
        # the data may not parse as the above statement is expecting. Well,
        # it's not an error, so:
        return False


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


class TestValidationError(HttpTest):
    """basic tests for input validation."""

    def setUp(self):
        HttpTest.setUp(self)

        @rest.rest_call('POST', '/give-me-an-e', Schema({
            'foo': basestring,
            'bar': basestring,
        }))
        def api_call(foo, bar):
            pass

        @rest.rest_call('PUT', '/mixed/args/<arg1>', Schema({
            'arg1': basestring,
            'arg2': basestring,
        }))
        def mixed_args(arg1, arg2):
            return json.dumps([arg1, arg2])

        @rest.rest_call('PUT', '/custom-schema', schema=Schema({
            "the_value": int,
        }))
        def custom_schema(the_value):
            return repr(the_value)

    def _do_request(self, data):
        """Make a request to the endpoint with `data` in the body.

        `data` should be a string -- the server will expect valid json, but
        we want to write test cases with invalid input as well.
        """
        resp = self.client.post('/give-me-an-e', data=data)
        return resp

    def test_ok(self):
        assert not _is_error(self._do_request(json.dumps({'foo': 'alice',
                                                          'bar': 'bob'})),
                             rest.ValidationError)

    def test_bad_json(self):
        # Illegal JSON gets caught by flask itself, before we get to look at
        # it. As such, the resulting error isn't an instance of APIError, so
        # we can't use  `_is_error` here.
        resp = self._do_request('xploit')
        assert resp.status_code == 400

    def test_missing_bar(self):
        assert _is_error(self._do_request(json.dumps({'foo': 'hello'})),
                         rest.ValidationError)

    def test_extra_baz(self):
        assert _is_error(self._do_request(json.dumps({'foo': 'alice',
                                                      'bar': 'bob',
                                                      'baz': 'eve'})),
                         rest.ValidationError)

    def test_mixed_args_ok(self):
        """Test a call that has arguments in both the url and body."""
        resp = self.client.put('/mixed/args/foo',
                               data=json.dumps({'arg2': 'bar'}))
        assert resp.status_code == 200
        assert json.loads(resp.get_data()) == ['foo', 'bar']

    def test_custom_schema(self):
        assert _is_error(self.client.put('/custom-schema', data=json.dumps({
            'the_value': 'Not an integer!',
        })), rest.ValidationError)


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
