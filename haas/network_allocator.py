"""Network allocator

This module supplies an interface for an allocator of network identifiers to
be used by API calls such as ``network_create``.

For HaaS to operate correctly, a network allocator must be registered by
calling ``set_network_allocator`` exactly once -- typically this is done by an
extension.
"""

import sys
from abc import ABCMeta, abstractmethod


class NetworkAllocator(object):
    """A network allocator allocates network identifiers for use by HaaS.

    A network identifier is an implementation-specific string that is treated
    as opaque by the HaaS core.

    This class is abstract; extensions should subclass it and provide the
    specified methods, then call ``set_network_allocator`` to register the
    allocator.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_new_network_id(self, db):
        """Gets a new network ID, valid for this driver.  Returns 'None' if there
        are no more possible IDs available.  Pass in the database connection, to
        make the allocation part of the current transaction.
        """

    @abstractmethod
    def free_network_id(self, db, net_id):
        """Marks a network ID as unused, so that it can be re-used for a new
        network.  Can be a no-op on some drivers.  Pass in the database
        connection, to make the freeing part of the current transaction.
        """

    @abstractmethod
    def populate(self, db):
        """Populate the database with any initial state needed by the allocator.

        This is invoked once when the haas database is first initialized.
        """

_network_allocator = None


def set_network_allocator(network_allocator):
    """Set the current network allocator to ``network_allocator``.

    This function must be called exactly once, typically from the extension
    providing the network allocator. If it is called more than once, or has
    not been called by the time all extensions have been loaded, HaaS will
    exit with an error.
    """
    global _network_allocator
    if _network_allocator is not None:
        sys.exit("Fatal Error: set_network_allocator() called twice. Make sure "
                 "you don't have conflicting extensions loaded.")
    _network_allocator = network_allocator


def get_network_allocator():
    return _network_allocator
