HaaS supports different types of devices (like network switches, out of band
management controllers) through a driver model. This document describes the
general concepts of that driver model and where it is currently applied.

The HaaS API manipulates each type of device (currently just network devices)
through the same set of API calls, meaning that code within the main HaaS tree
need not worry about platform-specific details (like how to add a
VLAN to a Cisco 5500 switch port).

Most objects within HaaS are persisted to the database, and thus classes map to
tables. The driver makes use of SQLAlchemy's `joined table inheritance
<https://sqlalchemy.readthedocs.org/en/rel_0_9/orm/inheritance.html>`_ to map
class hierarchies to the database.

Each type of object that supports different drivers has a top-level superclass,
e.g. ``Switch`` or ``OBM``, and the drivers themselves are subclasses of that
superclass (typically defined from within extensions). Under most
circumstances, SQLAlchemy makes this "just work"; when fetching the object from
the database, the right subclass will be automatically used. However, when
*creating* an object for the first time, HaaS must be told which driver to use
(is the switch a powerconnect or a nexus?). For these cases, the api calls in
question (node_register, switch_register...) will expect a type field to be
provided. The module ``haas.class_resolver`` provides facilities for finding
the appropriate subclass based on the contents of this type field.

The switch drivers shipped with HaaS itself are defined in the modules beneath
``haas.ext.switches``. These include drivers for the Dell Powerconnect
5500-series (in ``haas.ext.switches.dell``) and the Cisco Nexus 5500 (
``haas.ext.switches.nexus``), as well as a mock driver useful for testing
(``haas.ext.switches.mock``).
