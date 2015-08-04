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
"""Module `rest` provides a wsgi application implementing a REST API.

The function `wsgi_handler` is the wsgi entry point to the app.

The decorator `rest_call` and the classes `APIError` and `ServerError`
are the main things of interest in this module.
"""
import logging
import inspect
import json

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule, parse_rule
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.local import Local, LocalManager

from schema import Schema, SchemaError

local = Local()
local_manager = LocalManager([local])

logger = logging.getLogger(__name__)

_url_map = Map()


class APIError(Exception):
    """An exception indicating an error that should be reported to the user.

    i.e. If such an error occurs in a rest API call, it should be reported as
    part of the HTTP response.
    """
    status_code = 400  # Bad Request

    def response(self):
        # TODO: We're getting deprecation errors about the use of self.message.
        # We should figure out what the right way to do this is.
        return Response(json.dumps({'type': self.__class__.__name__,
                                    'msg': self.message,
                                    }), status=self.status_code)


class ServerError(Exception):
    """An error occurred when trying to process the request.

    This is likely not the client's fault; as such the HTTP status is 500.
    The semantics are much the same as the corresponding HTTP error.

    In general, we do *not* want to report the details to the client,
    though we should log them for our own purposes.
    """
    status_code = 500


class ValidationError(APIError):
    """An exception indicating that the body of the request was invalid."""


def rest_call(method, path, schema=None):
    """A decorator which registers an http mapping to a python api call.

    `rest_call` makes no modifications to the function itself, though the
    function need not worry about most of the details of the http request, see
    below for details.

    Arguments:

    * path - the url-path to map the function to. The format is the same as for
            werkzeug's router (e.g. '/foo/<bar>/baz')
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
            _schema = _make_schema_for(path, f)
        else:
            _schema = schema
        _url_map.add(Rule(path, endpoint=(f, _schema), methods=[method]))
        return f
    return register


def _make_schema_for(path, func):
    """Build a default schema for `func` at `path`.

    `func` is an api function.
    `path` is a url path, as recognized by werkzeug's router.

    `_make_schema_for` will build a schema to validate the body of a request,
    which will expect the body to be a json object whose keys are (exactly)
    the set of positional arguments to `func` which cannot be drawn from
    `path`, and whose values are strings.

    If all of the arguments to `func` are accounted for by `path`,
    `_make_schema_for` will return `None` instead.
    """
    path_vars = [var for (converter, args, var) in parse_rule(path)
                 if converter is not None]
    argnames, _, _, _ = inspect.getargspec(func)
    schema = dict((name, basestring) for name in argnames)
    for var in path_vars:
        del schema[var]
    if schema == {}:
        return None
    return Schema(schema)


def _format_arglist(*args, **kwargs):
    """Format the argument list in a human readable way.

    Should look pretty much like what you'd see in the source, e.g.
    (1, "hello", foo=[1,2])
    """
    args = list(args)
    for k, v in kwargs.iteritems():
        args.append('%s=%r' % (k, v))
    return ', '.join(args)


def request_handler(request):
    """Handle an http request.

    The parameter `request` must be an instance of werkzeug's `Request` class.
    The return value will be a werkzeug `Response` object.
    """
    adapter = _url_map.bind_to_environ(request.environ)
    try:
        (f, schema), values = adapter.match()
        if schema is None:
            # no data needed from the body:
            request_data = {}
            # XXX: It would be nice to detect if the body is erroneously
            # non-empty, which is probably indicitave of a bug in the client.
        else:
            try:
                # Parse the body as json and validate it with the schema:
                request_handle = request.environ['wsgi.input']
                request_json = request_handle.read(request.content_length)
                request_data = schema.validate(json.loads(request_json))
                if not isinstance(request_data, dict):
                    raise ValidationError("The body of the request is not a JSON object.")
            except ValueError:
                # Parsing the json failed.
                raise ValidationError("The body of the request is not valid JSON.")
            except SchemaError:
                # Validating the schema failed.

                # It would be nice to return a more helpful error message here, but
                # it's a little awkward to extract one from the exception. You can
                # easily get something like:
                #
                #   'hello' should be instance of <type 'int'>
                #
                # which, while fairly clear and helpful, is obviously talking about
                # python types, which is gross.
                raise ValidationError("The request body %r is not valid for "
                                        "this request." % request_json)
        for k, v in values.iteritems():
            if k in request_data:
                logger.error("Argument %r to api function %r exists in both "
                             "the URL path and the body of the request. "
                             "This is a BUG in the schema for %r; the schema "
                             "is responsible for eliminating this possibility.",
                             k, f.__name__, f.__name__)
                raise InternalServerError()
            request_data[k] = v
        logger.debug('Recieved api call %s(%s)', f.__name__, _format_arglist(**request_data))
        response_body = f(**request_data)
        result = f(**request_data)
        if result is None:
            response_body, status = "", 200
        elif type(result) is tuple:
            response_body, status = result
        else:
            # result is a string:
            response_body, status = result, 200
        logger.debug("completed call to api function %s, "
                     "response body: %r", f.__name__, response_body)
        return Response(response_body, status=status)
    except APIError as e:
        logger.debug('Invalid call to api function %s, raised exception: %r',
                     f.__name__, e)
        return e.response()
    except ServerError as e:
        logger.error('Server-side failure in function %s, raised exception: %r',
                     f.__name__, e)
        return InternalServerError()
    except HTTPException, e:
        return e


@local_manager.middleware
def wsgi_handler(environ, start_response):
    """The wsgi entry point to the API."""
    response = request_handler(Request(environ))
    return response(environ, start_response)

def serve(debug=True):
    """Start an http server running the API.

    This is intended for development purposes *only* -- as such the default is
    to turn on the debugger (which allows arbitrary code execution from the
    client!) and configure the server to automatically restart when changes are
    made to the source code. The `debug` parameter can be used to change this
    behavior.
    """
    from werkzeug.serving import run_simple
    run_simple('127.0.0.1', 5000, wsgi_handler,
               use_debugger=debug,
               use_reloader=debug)
