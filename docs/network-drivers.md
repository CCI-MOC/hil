# Network Drivers

This document describes the network driver model, primarily from a
system administrator's standpoint, though there are some details useful
for developers writing tools which interact with the API as well.

## Overview

There are two classes of network-related drivers: network allocators and
switches. Switches are straightforward to understand; they provide
support for a particular hardware switch. Network allocators are a
bit more abstract.

HIL networks may be backed by various underlying isolation technologies
(currently the only network allocator shipped with HIL uses 802.1q
VLANs, but there may be more, e.g. VXLANs in the future). A network
allocator manages the details of mapping networks created by HIL to
these underlying technologies. For example, the ``vlan_pool`` allocator
maps each network to a unique VLAN id.

Drivers are implemented as extensions, and must be added to the
``[extensions]`` section of ``hil.cfg``. You must supply *exactly* one
network allocator driver, and one or more switches. For example::

    ...
    [extensions]
    hil.ext.network_allocators.vlan_pool =
    hil.ext.switches.dell =
    hil.ext.switches.nexus =

Some drivers may also need driver specific options, which go in a
section with the same name as the extension, e.g.::

    [hil.ext.network_allocators.vlan_pool]
    vlans = 300-500, 700-750

## Network allocator drivers

The only network allocator shipped with HIL that is of interest to
users (there are others useful for development purposes) is the VLAN
allocator. The name of the extension is
``hil.ext.network_allocators.vlan_pool``, and it requires a single
extension-specific config option, `vlans`, which is a comma separated
list of VLAN ids and/or ranges of VLAN ids. Networks created within HIL
will use VLANs specified in the configuration file. An example::

    ...

    [extensions]
    hil.ext.network_allocators.vlan_pool =
    ...

    [hil.ext.network_allocators.vlan_pool]
    vlans = 300, 500-700, 800-950
    ...

Once HIL has been started, removing VLANs from this list is *not*
supported. You may add additional VLANs, but you will have to re-run
``hil-admin db create``.

## Security

It is VERY IMPORTANT that you be sure to configure your switches to
guard against VLAN hopping attacks:

    https://en.wikipedia.org/wiki/VLAN_hopping

Doing so is not difficult, and it is critical for security.

## Switch drivers

At present, all switch drivers shipped with HIL require that the VLAN
pool allocator is in use. There are five switch drivers shipped with
HIL:

* ``hil.ext.switches.dell``, which provides a driver for the Dell
  Powerconnect 5500 series switches.
* ``hil.ext.switches.n3000``, which provides a driver for the Dell N3000
  series switches.
* ``hil.ext.switches.nexus``, which provides a driver for some Cisco
  Nexus switches. Only the 3500 and 5500 have been tested, though it is
  possible that other models will work as well.
* ``hil.ext.switches.brocade``, for the brocade VDX 6740.
* ``hil.ext.switches.n3000``, for Dell N3000 series switches.
* ``hil.ext.switches.dellnos9``, for Dell switches running Dell Networking OS 9.

Different switches may or may not have certain capabilities. The `show_switch` call
can be used to see what a switch is capable of. Currently, HIL exposes the
following switch capabilities:

* `nativeless-trunk-mode` : If supported, a switchport can be configured to have
no native networks in trunk mode. If not supported, then the switchport must be
first connected to a native network before adding any tagged VLANs.


Per the information in `rest_api.md`, the details of certain API calls are
driver-dependant, below are the details for each of these switches.

### Powerconnect 5500 driver

#### Switch preparation

A few commands are necessary to run on the switch before it can be used with HIL.

1. Every VLAN that could be used on the switch must first be enabled on the switch itself. This is distinct from adding a VLAN to a port. To enable all VLANs to work with the switch, run this command (note that it seems to time out or something, but it just takes a while):

   configure
   vlan 2-4094

2. This switch uses ssh for connection. Be sure that ssh is enabled on the switch.

#### switch_register

To register a Dell Powerconnect switch, the ``"type"`` field of the
request body must have a value of::

    http://schema.massopencloud.org/haas/v0/switches/powerconnect55xx

In addition, it requires three extra fields: ``"username"``,
``"hostname"``, and ``"password"``, which provide the necessary
information to connect to the switch via telnet (``"hostname"`` may also
be an IP address).  SSH support is planned, but even so we do not
recommend allowing connectivity to a switch's management interface from
an untrusted network.

#### switch_register_port

Port names must be of the same form accepted by the switch's console
interface, e.g. ``gi1/0/5``. Be *very* careful when specifying these, as
they are not validated by HIL (this will be fixed in future versions).

### Dell N3000 driver

#### Switch preparation

1. Just like the Powerconnect 5500, every VLAN that could be used on the switch
must first be enabled on the switch. To enable all VLANs to work with the switch, run this command:

```
   # configure
   # vlan 2-4093
```

2. HIL uses ssh to connect to these switches. Configure the switch to accept ssh connections.

#### switch_register

To register a Dell N3000 switch, the ``"type"`` field of the
request body must have a value of::

    http://schema.massopencloud.org/haas/v0/switches/delln3000

It requires the same fields as the powerconnect driver, plus an
additional field "dummy_vlan" like the nexus driver, which should be a JSON
number corresponding to an unused VLAN id on the switch. Unlike the nexus
switch, this dummy vlan must exist otherwise you cannot set it as the native
vlan, but this vlan should not be used for any networks.

#### switch_register_port

Register ports just like the powerconnect driver. e.g. ``gi1/0/5``.

### Nexus driver

#### Switch preparation

This switch uses ssh for connection. Be sure that ssh is enabled on the switch.

#### switch_register

The type field for the Nexus driver has the value::

    http://schema.massopencloud.org/haas/v0/switches/nexus

The nexus driver requires the same additional fields as the powerconnect
driver, plus an additional field "dummy_vlan", which should be a JSON
number corresponding to an unused VLAN id on the switch. This VLAN
should be deactivated (and thus no traffic should flow across it ever).
This exists to get around an implementation problem related to disabling
the native VLAN.

For example, if you've chosen VLAN id 2222 to use as the dummy vlan, on
the switch's console, run:

    # config terminal
    # no vlan 2222

The body of the api call request can then look like:

    {
        "type": "http://schema.massopencloud.org/haas/v0/switches/nexus",
        "username": "MyUser",
        "password": "secret",
        "hostname": "mynexus.example.com",
        "dummy_vlan": 2222
    }

#### switch_register_port

Like the powerconnect driver, the Nexus driver accepts port names of the
same format accepted by the underlying switch, in this case (e.g.)
``ethernet 1/42``. The same concerns about validation apply.

### Brocade driver

#### switch_register

The ``type`` field for the Brocade NOS driver has the value:

    http://schema.massopencloud.org/haas/v0/switches/brocade

In addition to ``type``, the brocade driver requires three additional fields
``hostname``, ``username``, ``password``, and ``interface_type``.
``interface_type`` refers to the type and speed of the ports on the switch,
ex. "TenGigabitEthernet", "FortyGigabitEthernet". If you have multiple types
of ports on the same switch, register the switch multiple times with different
parameters for ``interface_type``.

The body of the api call request will look like:

    {
        "type": "http://schema.massopencloud.org/haas/v0/switches/brocade",
        "username": "MyUser",
        "password": "secret",
        "hostname": "mybrocade.example.com",
        "interface_type": "TenGigabitEthernet"
    }

#### switch_register_port

The brocade driver accepts interface names the same way they would be accepted
in the console of the switch, ex. ``101/0/10``.

### Dell Networking OS 9 driver

#### switch_register

The ``type`` field for the Dell Networking OS 9 driver has the value:

    http://schema.massopencloud.org/haas/v0/switches/dellnos9

In addition to ``type``, you need to supply ``username``, ``password``,
``hostname``, and ``interface_type``. ``interface_type`` is of the form
"GigabitEthernet", "TenGigabitEthernet". Please look at the switch guide for
more valid interface types.

The switch's API server either runs on port 8008 (HTTP) or 8888 (HTTPS), so be
sure to specify that in the ``hostname``.

This switch must have a native VLAN connected first before having any trunked
VLANs. The switchport is turned on only when a native VLAN is connected.

If you have multiple types of ports on the same switch, register the switch
multiple times with different parameters for ``interface_type``.

The body of the api call request will look like:

    {
        "type": "http://schema.massopencloud.org/haas/v0/switches/dellnos9",
        "username": "MyUser",
        "password": "secret",
        "hostname": "switch.example.com:8008",
        "interface_type": "GigabitEthernet"
    }

#### switch_register_port

It accepts interface names the same way they would be accepted in the console
of the switch, ex. ``1/3``.

When a port is registered, ensure that it is turned off (otherwise it might be
sitting on a default native vlan). HIL will then take care of turning on/off
the port.

### Using multiple switches

Networks managed by HIL may span multiple switches. No special configuration
of HIL itself is required; just register each switch as normal and ensure that
all VLANs in the allocator's ``vlans`` option are trunked to every managed
switch.
