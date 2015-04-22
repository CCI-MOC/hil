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
from haas import rest

from abc import ABCMeta, abstractmethod
from StringIO import StringIO
import unittest
import json
import sys

from werkzeug.routing import Map
from werkzeug.wrappers import Request

from schema import Schema, Optional

# We don't directly use this, but unless we import it, the coverage tool
# complains and doesn't give us a report.
import pytest


def wsgi_mkenv(method, path, data=None):
    """Helper routine to build a wsgi environment.

    We need this to generate mock requests.
    """
    env = {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'SERVER_NAME': 'haas.test-env',
        'SERVER_PORT': '5000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.errors': sys.stderr,
        'wsgi.multithreaded': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    if data is None:
        env['wsgi.input'] = StringIO()
    else:
        env['wsgi.input'] = StringIO(data)
    return env


class HttpTest(unittest.TestCase):
    """A test which excercises the http server.

    HttpTests run with no api functions registered to the http server yet;
    this lets us test the http-related code in an environment that is not
    constrained by our actual api.
    """

    def setUp(self):
        # We back up the old _url_map, and restore it in tearDown; this makes
        # it easy to be sure that we're not interfering with other tests:
        self.old_url_map = rest._url_map
        # We make ourselves an empty one for our test:
        rest._url_map = Map()

    def tearDown(self):
        rest._url_map = self.old_url_map


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
        """Return a request which will invoke the api call.

        The request should take the form of a WSGI v1.0 environment.
        The function `wsgi_mkenv` can be used to build a suitable
        environment.
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
        req = Request(self.request())
        resp = rest.request_handler(req)
        body = resp.get_data()
        self.api_teardown()

        # Now call it directly.
        try:
            self.api_setup()
            ret = self.api_call()
            assert resp.status_code == 200
            if ret == '':
                assert body == ''
            else:
                assert json.loads(body) == json.loads(ret)
        except rest.APIError, e:
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

        @rest.rest_call('GET', '/func/<foo>/<bar>')
        def func(foo, bar):
            return json.dumps([foo, bar])

    def api_call(self):
        return json.dumps(['alice', 'bob'])

    def request(self):
        return wsgi_mkenv('GET', '/func/alice/bob')


class TestBodyArgs(HttpEquivalenceTest, HttpTest):
    """Test that arguments supplied in the body are passed correctly."""

    def setUp(self):
        HttpTest.setUp(self)

        @rest.rest_call('POST', '/func/foo')
        def foo(bar, baz):
            return json.dumps([bar, baz])

    def api_call(self):
        return json.dumps(['bonnie', 'clyde'])

    def request(self):
        return wsgi_mkenv('POST', '/func/foo',
                          data=json.dumps({'bar': 'bonnie', 'baz': 'clyde'}))


class TestRestCallSchema(HttpEquivalenceTest, HttpTest):
    """Test that an alternate schema is used if one is provided to rest_call."""

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
        return wsgi_mkenv('POST', '/product',
                            data=json.dumps({'x': 2, 'y': 7}))


class TestEquiv_basic_APIError(HttpEquivalenceTest, HttpTest):
    """Basic test to make sure the APIError handling code is excercised."""

    def setUp(self):
        HttpTest.setUp(self)

        @rest.rest_call('GET', '/some_error')
        def some_error():
            self.api_call()

    def api_call(self):
        raise rest.APIError("Basic test of the APIError code.")

    def request(self):
        return wsgi_mkenv('GET', '/some_error')


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


class TestValidationError(HttpTest):
    """basic tests for input validation."""

    def setUp(self):
        HttpTest.setUp(self)

        @rest.rest_call('POST', '/give-me-an-e')
        def api_call(foo, bar):
            pass

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
        req = Request(wsgi_mkenv('POST', '/give-me-an-e', data=data))
        return rest.request_handler(req)

    def test_ok(self):
        assert not _is_error(self._do_request(json.dumps({'foo': 'alice',
                                                          'bar': 'bob'})),
                             rest.ValidationError)

    def test_bad_json(self):
        assert _is_error(self._do_request('xploit'), rest.ValidationError)

    def test_missing_bar(self):
        assert _is_error(self._do_request(json.dumps({'foo': 'hello'})),
                         rest.ValidationError)

    def test_extra_baz(self):
        assert _is_error(self._do_request(json.dumps({'foo': 'alice',
                                                      'bar': 'bob',
                                                      'baz': 'eve'})),
                         rest.ValidationError)

    def test_custom_schema(self):
        assert _is_error(self._do_request(json.dumps({
            'the_value': 'Not an integer!',
        })), rest.ValidationError)
