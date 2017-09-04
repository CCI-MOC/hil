# Copyright 2013-2015 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.
"""Exceptions thrown by HIL api calls.

This module defines several exceptions corresponding to specific errors.
They fall into two basic categories, captured by the classes APIError
and ServerError.
"""

import json
import flask
from werkzeug.exceptions import HTTPException, InternalServerError


class APIError(HTTPException):
    """An exception indicating an error that should be reported to the user.

    i.e. If such an error occurs in a rest API call, it should be reported as
    part of the HTTP response.
    """
    status_code = 400  # Bad Request

    def __init__(self, message=''):
        # HTTPException has its own custom __init__ method, but we want the
        # usual "First argument is the message" behavior.
        HTTPException.__init__(self)
        self.message = message

    def get_response(self, environ=None):
        """The body of the http response corresponding to this error."""
        # TODO: We're getting deprecation errors about the use of self.message.
        # We should figure out what the right way to do this is.
        return flask.make_response(json.dumps({
            'type': self.__class__.__name__,
            'msg': self.message,
        }), self.status_code)


class ServerError(InternalServerError):
    """An error occurred when trying to process the request.

    This is likely not the client's fault; as such the HTTP status is 500.
    The semantics are much the same as the corresponding HTTP error.

    In general, we do *not* want to report the details to the client,
    though we should log them for our own purposes.
    """


class NotFoundError(APIError):
    """An exception indicating that a given resource does not exist."""
    status_code = 404  # Not Found


class DuplicateError(APIError):
    """An exception indicating that a given resource already exists."""
    status_code = 409  # Conflict


class AllocationError(ServerError):
    """An exception indicating resource exhaustion."""


class BadArgumentError(APIError):
    """An exception indicating an invalid request on the part of the user."""


class ProjectMismatchError(APIError):
    """An exception indicating that the resources given don't belong to the
    same project.
    """
    status_code = 409  # Conflict


class AuthorizationError(APIError):
    """An exception indicating that the user is not authorized to perform
    the requested action.
    """
    status_code = 401


class BlockedError(APIError):
    """An exception indicating that the requested action cannot happen until
    some other change.  For example, deletion is blocked until the components
    are deleted, and possibly until the dirty flag is cleared as well.
    """
    status_code = 409  # Conflict


class IllegalStateError(APIError):
    """The request is invalid due to the state of the system.

    The request might be perfectly valid in another context. For example,
    trying to remove a nic from a running headnode might raise this error.
    """
    status_code = 409  # Conflict


class OBMError(ServerError):
    """An error occured communicating with the OBM for a node."""
