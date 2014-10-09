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

The decorator `rest_call` and the class `APIError` are the main things of
interest in this module.
"""
import logging
import inspect
import json

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule, parse_rule
from werkzeug.exceptions import HTTPException, InternalServerError

from schema import Schema

logger = logging.getLogger(__name__)

_url_map = Map()


MAX_CONTENT_LENGTH = 8192


class APIError(Exception):
    """An exception indicating an error that should be reported to the user.

    i.e. If such an error occurs in a rest API call, it should be reported as
    part of the HTTP response.
    """
    status_code = 400 # Bad Request

class MissingArgumentError(APIError):
    """Indicates that a required parameter was missing from the request."""
    # This is only used within this module; arguably we should be giving it a
    # name that suggest being private, e.g. _MissingArgumentError, but we're
    # handing the class name back to the client, so we leave it as something
    # less peculiar for now.


def rest_call(method, path):
    """A decorator which registers an http mapping to a python api call.

    `rest_call` makes no modifications to the function itself, though the
    function need not worry about most of the details of the http request, see
    below for details.

    Arguments:

    path - the url-path to map the function to. The format is the same as for
           werkzeug's router (e.g. '/foo/<bar>/baz')
    method - the HTTP method for the api call (e.g. POST, GET...)

    Any parameters to the function not designated in the url will be pulled
    from a json object in the body of the requests.

    For example, given:

        @rest_call('POST', '/some-url/<baz>/<bar>')
        def foo(bar, baz, quux):
            pass

    When a POST request to /some-url/*/* occurs, `foo` will be invoked
    with its bar and baz arguments pulled from the url, and its quux from
    the body. So, the request:

        POST /some-url/alice/bob HTTP/1.1
        <headers...>

        {"quux": "eve"}

    Will invoke `foo('alice', 'bob', 'eve')`.

    If the function raises an `APIError`, the error will be reported to the
    client with the exception's status_code attribute as the return status, and
    a json object such as:

        {
            "type": "MissingArgumentError",
            "msg": "The required argument FOO was not supplied."
        }

    as the body, i.e. `type` will be the type of the exception, and `msg`
    will be a human-readable error message.
    """
    def register(f):
        schema = _make_schema_for(path, f)
        _url_map.add(Rule(path, endpoint=(f, schema), methods=[method]))
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


def request_handler(request):
    """Handle an http request.

    The parameter `request` must be an instance of werkzeug's `Request` class.
    The return value will be a werkzeug `Response` object.
    """
    adapter = _url_map.bind_to_environ(request.environ)
    try:
        (f, schema), values = adapter.match()

        if schema is not None:
            # Make sure we don't get DOS'd by a huge request body:
            request_body = request.environ['wsgi.input']
            request_body = request_body.read(MAX_CONTENT_LENGTH)

            # Parse the body as json and validate it with the schema:
            request_body = schema.validate(json.loads(request_body))
        else:
            # Nothing is needed from the body. We set it to an empty dict:
            request_body = {}

        # marshall the arguments to the api call from the request, and then
        # call it. See the docstring for rest_call for more explanation.
        argnames, _, _, _ = inspect.getargspec(f)
        positional_args = []
        for name in argnames:
            if name in values:
                positional_args.append(values[name])
            elif name in request_body:
                positional_args.append(request_body[name])
            else:
                logger.error("The required parameter %r to api call %s was "
                             "missing from the request, but the schema didn't "
                             "catch it! This is a bug!", name, f.__name__)
                raise InternalServerError()

        logger.debug('Recieved api call %s(%s)',
                     f.__name__,
                     ', '.join([repr(arg) for arg in positional_args]))
        response_body = f(*positional_args)
        if not response_body:
            response_body = ""
        logger.debug("completed call to api function %s, "
                     "response body: %r", f.__name__, response_body)
        return Response(response_body, status=200)
    except APIError, e:
        # TODO: We're getting deprecation errors about the use of e.message. We
        # should figure out what the right way to do this is.
        logger.debug('Invalid call to api function %s, raised exception: %r',
                     f.__name__, e)
        return Response(json.dumps({
                'type': e.__class__.__name__,
                'msg': e.message,
            }), status=e.status_code)
    except HTTPException, e:
        return e


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

    serve()
