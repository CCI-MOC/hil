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
"""Module `rest` provides a flask application implementing a REST API.

The main things of interest in this module are:

    * `app`, the flask application itself.
    * The decorator `rest_call`
    * The variable `local`. `local.db` is a SQLAlchemy session object which
      is local to the current request. It is cleaned up automatically when the
      request finishes (rolling back any changes which have not been comitted).
"""
import logging
import inspect

import flask

from haas.errors import APIError, ServerError, AuthorizationError
from haas.config import cfg

from schema import Schema, SchemaError

from haas import auth
from haas.model import Session

app = flask.Flask(__name__.split('.')[0])
local = flask.g

logger = logging.getLogger(__name__)


class ValidationError(APIError):
    """An exception indicating that the body of the request was invalid."""


def rest_call(method, path, schema=None):
    """A decorator which registers an http mapping to a python api call.

    `rest_call` makes no modifications to the function itself, though the
    function need not worry about most of the details of the http request, see
    below for details.

    Arguments:

    * path - the url-path to map the function to. The format is the same as for
            flask's router (e.g. '/foo/<bar>/baz')
    * method - the HTTP method for the api call (e.g. POST, GET...)
    * schema (optional) - an instance of ``schema.Schema`` with which to
            validate the body of the request. It should assume its argument is
            a JSON object, represented as a python ``dict``.

            If this is omitted, ``moc-rest`` will generate a schema which
            verifies that all of the expected arguments exist and are strings
            (see below).

            ``schema`` MUST ensure that none of the arguments in ``path`` are
            also found in the body of the request.

    Any parameters to the function not designated in the url will be pulled
    from a json object in the body of the requests.

    For example, given::

        @rest_call('POST', '/some-url/<bar>/<baz>')
        def foo(bar, baz, quux):
            pass

    When a POST request to ``/some-url/*/*`` occurs, ``foo`` will be invoked
    with its ``bar`` and ``baz`` arguments pulled from the url, and its
    ``quux`` from the body. So, the request::

        POST /some-url/alice/bob HTTP/1.1
        <headers...>

        {"quux": "eve"}

    Will invoke ``foo('alice', 'bob', 'eve')``.

    If the function raises an `APIError`, the error will be reported to the
    client with the exception's status_code attribute as the return status, and
    a json object such as:

        {
            "type": "MissingArgumentError",
            "msg": "The required argument FOO was not supplied."
        }

    as the body, i.e. `type` will be the type of the exception, and `msg`
    will be a human-readable error message.

    If no exception is raised, the return value must be one of:

        * None (implicit if there's no ``return`` statement), in which case
          the response code will be 200 and the body will be empty
        * A string, which will be used as the body of the response. again,
          the status code will be 200.
        * A tuple, whose first element is a string (the response body), and
          whose second is an integer (the status code).
    """
    def register(f):
        if schema is None:
            _schema = _make_schema_for(f)
        else:
            _schema = schema
        app.add_url_rule(path,
                         f.__name__,
                         _rest_wrapper(f, _schema),
                         methods=[method])
        return f
    return register


def _make_schema_for(func):
    """Build a default schema for the api function `func`.

    `_make_schema_for` will build a schema to validate the arguments to an
    API call, which will expect each argument to be a string. Any arguments
    not found in the url will be pulled from a JSON object in the body of a
    request.

    If all of the arguments to `func` are accounted for by `path`,
    `_make_schema_for` will return `None` instead.
    """
    argnames, _, _, _ = inspect.getargspec(func)
    return Schema(dict((name, basestring) for name in argnames))


def _do_validation(schema, kwargs):
    """Validate the current request against `schema`.

    `schema` should be a schema as passed to `rest_call`.

    `kwargs` should be the arguments to the API call pulled from the URL.

    If the schema validates, this will return a dictioiniary of *all* of the
    arguments to the function, both from the URL and the body. The argument
    `kwargs` may be distructively updated.

    If the schema does not validate, this will raise an instance of
    `ValidationError`.
    """

    def _validates(value):
        """Retrun true if `schema` validates `value`, False otherwise.

        The schema library's `validate` method raises an exception, which is
        nice for short-circuting when just doing a simple check, but a bit
        awkward in more complex cases like the below.
        """
        try:
            schema.validate(value)
        except SchemaError:
            return False
        return True

    if schema is None or _validates(kwargs):
        return kwargs

    # One innocuous reason validation can fail is simply that we
    # need parameters from the body (in json). Let's get those and
    # try again.
    #
    # Without `force=True`, this will fail unless the
    # "Content-Type" header is set to "application/json". We'll be
    # a little more lienient here; we can discuss whether we want
    # to tighten this up later, but this makes mucking around with
    # curl less annoying, and is consistent with pre-flask
    # behavior.
    body = flask.request.get_json(force=True)

    validation_error = ValidationError(
        "The request body %r is not valid for "
        "this request." % body)
    for k in body.keys():
        if k in kwargs:
            raise validation_error  # Duplicate key in body + url
        kwargs[k] = body[k]
    if not _validates(kwargs):
        # It would be nice to return a more helpful error message
        # here, but it's a little awkward to extract one from the
        # schema library. You can easily get something like:
        #
        #   'hello' should be instance of <type 'int'>
        #
        # which, while fairly clear and helpful, is obviously
        # talking about python types, which is gross.
        raise validation_error
    return kwargs


def _rest_wrapper(f, schema):
    """Return a wrapper around `f` that does the following:

    * Validate the current request agains the schema.
    * Implement the exception handling described in the documentation to
      `rest_call`.

    The result of this is suitable to hand directly to flask.
    """

    def wrapper(**kwargs):
        kwargs = _do_validation(schema, kwargs)
        logger.debug('Got api call: %s(%s)' %
                        (f.__name__, _format_arglist(**kwargs)))
        with DBContext():
            init_auth()
            return f(**kwargs)
    return wrapper


def _format_arglist(*args, **kwargs):
    """Format the argument list in a human readable way.

    Should look pretty much like what you'd see in the source, e.g.
    (1, "hello", foo=[1,2])
    """
    args = list(args)
    for k, v in kwargs.iteritems():
        args.append('%s=%r' % (k, v))
    return ', '.join(args)


class DBContext(object):
    """Context manager to set up a database session for the request handler

    This is used internally by the request handler, but is exposed to make
    testing easier.
    """

    def __enter__(self):
        local.db = Session()

    def __exit__(self, exc_type, exc_value, traceback):
        local.db.close()


def init_auth():
    ok = auth.get_auth_backend().authenticate()
    if cfg.has_option('auth', 'require_authentication'):
        require_auth = cfg.getboolean('auth', 'require_authentication')
    else:
        require_auth = True
    if not ok and require_auth:
        raise AuthorizationError("Authentication failed. Authentication "
                                 "is required to use this service.")


def serve(port, debug=True):
    """Start an http server running the API.

    This is intended for development purposes *only* -- as such the default is
    to turn on the debugger (which allows arbitrary code execution from the
    client!) and configure the server to automatically restart when changes are
    made to the source code. The `debug` parameter can be used to change this
    behavior.
    """
    app.run(port=port,
            use_debugger=debug,
            use_reloader=debug)
