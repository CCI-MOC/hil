"""Support module for looking up drivers by name

The driver model (see ``docs/driver-model.rst``) requires us to be able
to resolve driver names to classes; this module provides support for
building and querying lookup tables for this.

Any class which wishes to be exposed via this interface should:

1. Inherit, directly or inderectly, from the class defining the type of
   driver (e.g. Switch, OBM...)
2. have an attribute ``api_name``, which should be the name under which
   the class would like to be exposed.
"""


_class_map = {}


def concrete_class_for(superclass, name):
    """Looks up the concrete class registered under the name ``name``

    Returns the class, or None if not found.
    """
    if (superclass, name) in _class_map:
        return _class_map[(superclass, name)]
    else:
        return None


def build_class_map_for(superclass):
    """Build a lookup table for drivers implementing ``superclass``

    ``superclass`` should be a driver at the top level of a driver type
    class hierarchy. ``build_class_map_for`` then searches the class hierarchy
    beneath ``subclass``, registering each class which has an ``api_name``
    attribute.
    """
    def _add_to_class_map(cls):
        if hasattr(cls, 'api_name'):
            _class_map[(superclass, cls.api_name)] = cls
        for subclass in cls.__subclasses__():
            _add_to_class_map(subclass)
    for cls in superclass.__subclasses__():
        _add_to_class_map(cls)
