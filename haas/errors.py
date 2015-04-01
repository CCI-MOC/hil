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
"""Exceptions thrown by HaaS api calls.

This module defines several exceptions decending from haas.rest.APIError,
used for specific failures.
"""

from haas.rest import APIError


class NotFoundError(APIError):
    """An exception indicating that a given resource does not exist."""
    status_code = 404 # Not Found


class DuplicateError(APIError):
    """An exception indicating that a given resource already exists."""
    status_code = 409 # Conflict


class AllocationError(APIError):
    """An exception indicating resource exhaustion."""


class BadArgumentError(APIError):
    """An exception indicating an invalid request on the part of the user."""


class ProjectMismatchError(APIError):
    """An exception indicating that the resources given don't belong to the
    same project.
    """
    status_code = 409 # Conflict


class BlockedError(APIError):
    """An exception indicating that the requested action cannot happen until
    some other change.  For example, deletion is blocked until the components
    are deleted, and possibly until the dirty flag is cleared as well.
    """
    status_code = 409 # Conflict


class IllegalStateError(APIError):
    """The request is invalid due to the state of the system.

    The request might otherwise be perfectly valid.
    """
    status_code = 409 # Conflict


class ServerError(APIError):
    """An error occurred when trying to process the request.

    This likely not the client's fault; as such the HTTP status is 500.
    The semantics are much the same as the corresponding HTTP error.
    """
    status_code = 500
