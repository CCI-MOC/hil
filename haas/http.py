"""Module http handles all of the http-related logic for the HaaS.

HaaS is a wsgi application built on top of werkzeug. the function `wsgi_handler`
is the wsgi entry point to the app.

The decorator `rest_call` and the class `APIError` are the main things of
interest in this module.
"""
import logging
import inspect
from functools import wraps

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

_url_map = Map()

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
    from the form data.

    For example, given:

        @rest_call('POST', '/some-url/<baz>/<bar>')
        def foo(bar, baz, quux):
            pass

    When a POST request to /some-url/*/* occurs, `foo` will be invoked
    with its bar and baz arguments pulled from the url, and its quux from
    the form data in the body.

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
        _url_map.add(Rule(path, endpoint=f, methods=[method]))
        return f
    return register

def request_handler(request):
    """Handle an http request.

    The parameter `request` must be an instance of werkzeug's `Request` class.
    The return value will be a werkzeug `Response` object.
    """
    adapter = _url_map.bind_to_environ(request.environ)
    try:
        endpoint, values = adapter.match()

        # marshall the arguments to the api call from the request, and then
        # call it. See the docstring for rest_call for more explanation.
        argnames, _, _, _ = inspect.getargspec(endpoint)
        positional_args = []
        for name in argnames:
            if name in values:
                positional_args.append(values[name])
            elif name in request.form:
                positional_args.append(request.form[name])
            else:
                raise MissingArgumentError("The required parameter %r was "
                                           "missing from the form data." %
                                           name)
        logger.debug('Recieved api call %s(%s)',
                     endpoint.__name__,
                      ', '.join([repr(arg) for arg in positional_args]))
        resp = endpoint(*positional_args)

        # The api call can return nothing, just a body (as a string), or a body
        # and a status code. This is a holdover from our flask days, but it is
        # still sensible enough. We provide defaults for any missing
        # information:
        if isinstance(resp, tuple):
            body, status = resp
        else:
            body, status = resp, 200
        if not body:
            body = ""
        logger.debug("completed call to api function %s, "
                     "status: %d, body: %r", endpoint.__name__, status, body)
        return Response(body, status=status)
    except APIError, e:
        # TODO: We're getting deprecation errors about the use of e.message. We
        # should figure out what the right way to do this is.
        logger.debug('Invalid call to api function %s, raised exception: %r',
                     endpoint.__name__, e)
        return Response(json.dumps({
                'type': e.__class__.__name__,
                'msg': e.message,
            }), status=e.status_code)
    except HTTPException, e:
        return e

def wsgi_handler(environ, start_response):
    """The wsgi entry point to the HaaS."""
    response = request_handler(Request(environ))
    return response(environ, start_response)

def serve(debug=True):
    """Start an http server running the HaaS api.

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

if __name__ == '__main__':
    serve()
