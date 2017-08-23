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
    * The variable `local`, which is an alias for `flask.g`
"""
import logging
import json

import flask
from flask import _app_ctx_stack as ctx_stack

from hil.flaskapp import app
from hil.errors import APIError, AuthorizationError
from hil.config import cfg

from schema import SchemaError
from uuid import uuid4

from hil import auth

local = flask.g


class _RequestInfo(object):
    """A Flask extension that stores a few per request values.

    We use this in place of local because it allows the values to
    be generated dynamically, so

    * We don't need to do any extra work to make sure they're initialized
      in an app context.
    * We don't need to worry about dependency ordering (beyond making sure
      there are no cycles).

    """
    # For a description of how writing flask extensions works in general, see:
    #
    #     http://flask.pocoo.org/docs/0.11/extensiondev/
    #
    # Note that that document describes some compatability tricks for older
    # versions of flask; we don't bother with these.

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Standard init_app method for extensions; see the Flask documentation.
        """
        # We don't actually need to do anything here yet.

    @property
    def uuid(self):
        """A UUID identifying the request context."""
        ctx = ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'request_info_uuid'):
                ctx.request_info_uuid = uuid4()
            return ctx.request_info_uuid

request_info = _RequestInfo(app)


class ContextLogger(logging.LoggerAdapter):
    """Log adapter that adds context information to an underlying logger.

    If the ContextLogger is invoked from within a request context, the
    request context's uuid (from `request_info.uuid`) will be included in
    the output. Otherwise, the output will mention that it was invoked
    outside a request context.
    """

    def process(self, msg, kwargs):
        if request_info.uuid is None:
            return 'Outside request context: ' + msg, kwargs
        return 'In request context %s: %s' % (request_info.uuid, msg), kwargs


logger = ContextLogger(logging.getLogger(__name__), {})


class ValidationError(APIError):
    """An exception indicating that the body of the request was invalid."""


def rest_call(methods, path, schema, dont_log=()):
    """A decorator which registers an http mapping to a python api call.

    `rest_call` makes no modifications to the function itself, though the
    function need not worry about most of the details of the http request, see
    below for details.

    Arguments:

    * path - the url-path to map the function to. The format is the same as for
            flask's router (e.g. '/foo/<bar>/baz')
    * method - string representing the HTTP method (e.g. POST, GET...) for the
               api call or a list of such strings if the api call supports
               multiple HTTP methods.
    * schema - an instance of ``schema.Schema`` with which to
            validate the arguments to the function, whether specified in the
            URL or as JSON in the request body. The schema should expect
            a dictionary, where the keys are the names of the arguments. If
            a function argument has a default value, it may be marked as
            optional in the schema.

            Any arguments not found in the path will be assumed to be keys in a
            JSON object in the body of the request for non-GET requests. For
            GET requests, query parameters (ie - those appearing after '?') are
            also examined. It is an error for an argument to appear in two
            places (ie - the query parameters or body and the path); such
            requests will be rejected prior to invoking the schema.

            Because GET query parameters are initially strings, ensure that any
            GET arguments of non-string type implement Schema's "Use" to
            perform type validation and conversion.
    * dont_log (optional): a list of "sensitive" argument names, which should
            not be logged.

    For example, given::

        @rest_call('POST', '/some-url/<bar>/<baz>', Schema({
            'bar': basestring, 'baz': basestring,  'quux': basestring
        }))
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
        """Return value from rest call; this decorates the function itself."""

        if isinstance(methods, list):
            # Methods can be either passed as a single string
            # or a list. Use a separate local variable because
            # modifying `methods` gives an "UnboundLocalError"
            meths = methods
        else:
            meths = [methods]

        app.add_url_rule(path,
                         f.__name__,
                         _rest_wrapper(f, schema, dont_log),
                         methods=meths)
        return f
    return register


def _do_validation(schema, kwargs):
    """Validate the current request against `schema`.

    `schema` should be a schema as passed to `rest_call`.

    `kwargs` should be the arguments to the API call pulled from the URL.

    If the schema validates, this will return a dictionary of *all* of the
    arguments to the function, both from the URL and the body.

    If the schema does not validate, this will raise an instance of
    `ValidationError`.
    """

    final_kwargs = {}

    if flask.request.method == "GET":
        # GET requests can use path AND query parameter arguments
        if flask.request.data != '':
            raise ValidationError("GET request made with a non-empty request"
                                  " body")

        for key, value in flask.request.args.iteritems():
            if key in final_kwargs:
                raise ValidationError("Parameter specified more than once")
            elif value is None or value == '':
                # TODO: if we want to take flags (ie - an option that has no
                # value), change this check and add logic in the next else to
                # take care of that. We'll also need to pick a standard value
                # to represent a flag (like 'True', 'None' or '').
                raise ValidationError("Empty parameter specified")
            else:
                final_kwargs[key] = value
    else:
        # Methods other than GET can use path and body arguments
        if flask.request.data != '':
            try:
                final_kwargs = json.loads(flask.request.data)
            except ValueError:
                raise ValidationError("The request body is not valid JSON")

    validation_error = ValidationError(
            "Request arguments are not valid for this request")

    for k in kwargs.keys():
        if k in final_kwargs:
            raise validation_error
        final_kwargs[k] = kwargs[k]

    try:
        return schema.validate(final_kwargs)
    except SchemaError:
        # It would be nice to return a more helpful error message
        # here, but it's a little awkward to extract one from the
        # schema library. You can easily get something like:
        #
        #   'hello' should be instance of <type 'int'>
        #
        # which, while fairly clear and helpful, is obviously
        # talking about python types, which is gross.
        raise validation_error


def _rest_wrapper(f, schema, dont_log):
    """Return a wrapper around `f` that does the following:

    * Validate the current request against the schema.
    * Invoke the authentication backend
    * Implement the exception handling described in the documentation to
      `rest_call`.
    * Log arguments, except those in `dont_log`.
    * Convert `None` return values to empty bodies.

    The result of this is suitable to hand directly to flask.
    """

    def wrapper(**kwargs):
        """The wrapper described above."""
        kwargs = _do_validation(schema, kwargs)

        censored_kwargs = kwargs.copy()
        for argname in dont_log:
            censored_kwargs[argname] = '<<CENSORED>>'

        init_auth()
        logger.info('API call: %s(%s)',
                    f.__name__, _format_arglist(**censored_kwargs))

        ret = f(**kwargs)
        if ret is None:
            ret = ''
        return ret
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


def init_auth():
    """Process authentication.

    This invokes the auth backend. If HIL is configured to *require*
    authentication, and authentication fails, it raises an
    AuthorizationError.
    """
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
