"""Network allocator

This module supplies an interface for an allocator of network identifiers to
be used by API calls such as ``network_create``.

For HIL to operate correctly, a network allocator must be registered by
calling ``set_network_allocator`` exactly once -- typically this is done by an
extension.
"""

import sys
from abc import ABCMeta, abstractmethod


class NetworkAllocator(object):
    """A network allocator allocates network identifiers for use by HIL.

    A network identifier is an implementation-specific string that is treated
    as opaque by the HIL core.

    This class is abstract; extensions should subclass it and provide the
    specified methods, then call ``set_network_allocator`` to register the
    allocator.

    Instances of this class may expect to only be invoked from within a flask
    application context.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_new_network_id(self):
        """Gets a new network ID, valid for this driver.  Returns 'None' if there
        are no more possible IDs available.  Pass in the database connection,
        to make the allocation part of the current transaction.
        """

    @abstractmethod
    def free_network_id(self, net_id):
        """Marks a network ID as unused, so that it can be re-used for a new
        network.  Can be a no-op on some drivers.  Pass in the database
        connection, to make the freeing part of the current transaction.
        """

    @abstractmethod
    def populate(self):
        """Populate the database with any initial state needed by the allocator.

        This is invoked when the hil database is first initialized. It *must*
        be safe to call this method multiple times, including on a database
        that has been modified in ways during the course of normal HIL
        operation.
        """

    @abstractmethod
    def legal_channels_for(self, net_id):
        """Returns a list of legal channel specifications for ``net_id``.

        Note that this is not necessarily a list of each possible channel id;
        it may include wildcards. A consumer of the allocator should
        invoke ``is_legal_channel_for`` to check if a given identifier is
        legal.

        See ``docs/rest_api.md`` for details.
        """

    @abstractmethod
    def is_legal_channel_for(self, channel_id, net_id):
        """Returns True if ``channel_id`` is legal for ``net_id``,
        False otherwise.
        """

    @abstractmethod
    def get_default_channel(self):
        """Return the "default" channel which is used if a
        channel is unspecified.
        """
    @abstractmethod
    def validate_network_id(self, net_id):
        """Check if net_id is a valid network id"""

    @abstractmethod
    def claim_network_id(self, net_id):
        """Claim a network id when an admin creates a network"""

    @abstractmethod
    def is_network_id_in_pool(self, net_id):
        """returns true if net_id is part of the allocation pool"""


_network_allocator = None


def set_network_allocator(network_allocator):
    """Set the current network allocator to ``network_allocator``.

    This function must be called exactly once, typically from the extension
    providing the network allocator. If it is called more than once, or has
    not been called by the time all extensions have been loaded, HIL will
    exit with an error.
    """
    global _network_allocator
    if _network_allocator is not None:
        sys.exit("Fatal Error: set_network_allocator() called twice."
                 "Make sure you don't have conflicting extensions loaded.")

    _network_allocator = network_allocator


def get_network_allocator():
    """Return the network allocator.

    This may not be called before set_network_allocator.
    """
    return _network_allocator
