# OBM Drivers

This document describes the obm driver model.

## Overview

Out-of-Band Management (OBM) consists of separate channel dedicated for server maintenance.
It allows the systems-administrator to manage and monitor network-attached equipments remotely.
OBM allows operations like powering on, shutdown, reboot and knowing the status of the machines
regardless of whether the machine itself has an operating system or access to any network.

The Intelligent Platform Management Interface (IPMI) is one such OBM server protocol for which
HIL includes a driver. For developers, a null OBM driver is also included which can be activated
and used just like any other driver under HIL.


## Activating drivers under HIL

Drivers are implemented as extensions, and must be added to the
`[extensions]` section of `hil.cfg`. You can add as many OBM
drivers as are supported in your environment

for example::

    ...
    [extensions]
    hil.ext.obm.mock =
    hil.ext.obm.ipmi =


## IPMI driver

At present, only one driver of OBM type is supplied with HIL.
It is the IPMI driver.

* `hil.ext.obm.ipmi`, consist of the ipmi driver
    It does not require any driver specific configuration.

### Using IPMI driver

The type field for the IPMI driver has the value::

    http://schema.massopencloud.org/haas/v0/obm/ipmi


IPMI driver requires three additional feilds
to be able to communicate with the IPMI subsystem of a server.
These feilds are `host`, `user`, and `password`
These information is passed as a part of the `node_register` api call
when registering the node for the first time with HIL

For example, if a node with its ipmi-hostname as "ipmi_node01", ipmi-username as "ipmi-user01"
and ipmi-password as "pass1234" is to be registered with HIL.

The body of the api call request `node_register` can then look like::

    {"obm": { "type": "http://schema.massopencloud.org/haas/v0/obm/ipmi",
    		"host": "ipmi_node-01",
    		"user": "ipmi_user-01",
    		"password": "pass1234"
   	    }
    }

