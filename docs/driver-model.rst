HaaS supports different devices (e.g. switches, out of band management
controllers) Through a driver model. This document describes the general
concepts of that driver model.

The HaaS API manipulates each type of device through the same set of API
calls; power cycling nodes, configuring networks, etc. looks mostly the same
regardless of which switch the administrator has installed, or exactly what is
required to reboot a node programmatically.

Most objects within HaaS are persisted to the database, and thus classes map
to tables. The driver makes use of SQLAlchemy's joined table inheritance to
map class hierarchies to the database.

Each type of object that supports different drivers has a top-level
superclass, e.g. ``Switch`` or ``OBM``, and the drivers themselves are
subclasses of that superclass (typically defined from within extensions). Under
most curcumstances, SQLAlchemy makes this "just work"; when fetching the object
from the database, the right subclass will be instantiated, and everything will
"just work." However, when *creating* an object for the first time, HaaS must be
told which driver to use (is the switch a powerconnect or a nexus?) For these
cases, the api calls in question (node_register, switch_register...) will expect
a type field to be provided. The module ``haas.class_resolver`` provides
facilities for finding the appropriate subclass based on the contents of this
type field.
