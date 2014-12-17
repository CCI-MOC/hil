This document describes the proper configuration of the existing network
drivers.

In all cases, under the ``[general]`` section of ``haas.cfg``, set ``driver``,
to the driver you are using.  For VLAN-based drivers, you must have a section
``[vlan]``, with ``vlans`` set to a comma-delimited list of VLANS or ranges of
VLANs.  All further configuration belongs in the section ``[driver NAME]``,
where ``NAME`` is the name of the network driver being used.

# Single-switch driver using VLAN isolation (``simple_vlan``)

There is one configuration field: ``switch`` should be equal to a JSON object
representing the switch being used.  The object must have a field ``switch``
whose value is the switch driver being used (e.g. ``dell`` for Dell
Powerconnect switches).  The remaining fields are interpreted by that driver,
and will likely include the network location and administrator credentials for
the switch.

When creating a port while using this driver, name the port exactly what the
driver expects.  For example, in the case of the ``dell`` switch driver, this
will generally be something like ``gi1/1/15``.

When running the deployment tests, ``deployment.cfg`` has an additional value that
should be set: ``trunk_port`` is the name of the port that headnode traffic
runs on.  This port is always on all HaaS VLANs, so the deployment tests need
to know this port's identity in order to check that the switch is configured
correctly.

# Multiple-switch  driver using VLAN isolation (``complex_vlan``)

There is one configuration field: ``switches`` should be a JSON list of
objects, each representing one physical switch.  Each object must have a field
``switch``, the switch driver to be used, and ``name``, a unique identifier
that is used when specifying ports.  The remaining fields are used by the
switch driver.

When using this driver, name ports in the format ``[switch]::[port]``, where
``[switch]`` is the ``name`` field of the appropriate switch, and ``[port]``
is the port on the switch according to that switch's driver.  For example,
port ``gi1/1/15`` on switch ``dell-15`` would be named ``dell-15::gi1/1/15``.
There is not currently any provision for escaping a ``::`` in a switch or port
name.

When runnning deployment tests, ``deployment.cfg`` has an additional value
``trunk_ports``, a JSON-encoded list of port names.  This should contain all
ports that are set to trunk HaaS network traffic, either between switches or
to the HaaS headnode host.
