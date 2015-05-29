"""Network allocation pool

This module supplies a pool of network identifiers to be used by API calls such
as ``network_create``.

The ``network_pool`` variable will be used to allocate pools; an extension must
initialize that variable with an instance of ``NetworkPool``.
"""

from abc import ABCMeta, abstractmethod

class NetworkPool(object):
    """A network pool allocates network identifiers for internal use by HaaS.

    A network identifier is an implementation-specific string that is treated
    as opaque by the HaaS core.

    This class is abstract; extensions should subclass it and provide the
    specified methods, then assign an instance to ``network_pool``.
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

network_pool = None
