This document is a brief primer on 802.1q VLANs (Virtual LANs): what they are,
how switches tend to deal with them, how Linux deals with them, and how the
HaaS uses them.

# What are VLANs?

At a most basic level, a VLAN is simply a 12 bit tag in the header of an
ethernet packet, which can be used by networking equipment.

One typical use of VLANs is creating logical (virtual) networks, which can be
physically located on the same switch, but still isolated from one another.

# How do switches deal with VLANs?

Typically, traffic moving "through" a managed  switch will have a VLAN tag
associated with it, and will be distributed to all of the ports associated
with that VLAN. A port may be in one of two modes: access or trunking. (Some
switches have additional modes, but they are usually variations on one of
these, and inessential).

Access mode is the simpler of the two. For a port in access mode:

* The port is associated with exactly one VLAN tag.
* Any device(s) connected to the port do not and need not have any knowledge of
  the use VLANs.
* Any traffic coming in on the port has the associated VLAN tag added.
* Any traffic going out on the port has it's VLAN tag removed.

Access mode allows a port to be a member of a logical network without requiring
any knowledge of VLANs on the part of whatever is connected to the port.

In trunking mode:

* The port is associated with zero or more "tagged" VLANs.
* The port may also have one "native" VLAN.
* If an ethernet packet coming in on the port has no VLAN tag, then it is tagged
  with the "native" VLAN's tag.
* If an ethernet packet coming in on the port has a VLAN tag, then:
  * If that VLAN is associated with the port, it is left untouched, and
    distributed to the corresponding logical network as normal
  * Otherwise, the packet is dropped.
* Packets bound for VLANs which are "tagged" for the port retain their VLAN tags
  when going out on th port.
* TODO: my intuition is that packets bound for the native VLAN have their tags
  stripped off before exiting the port, but I'm not 100% sure of this.

Trunking mode could actually fully replace the functionality of access mode,
since a trunked port with just a native VLAN (and no tagged VLANs) is
equivalent. It is more flexible however.

# How does Linux deal with VLANs?

In a typical networking configuration, a Linux machine is not VLAN aware.
However, it is possible to create VLAN aware network interfaces with the
`vconfig` command. If `eth0` is a physical network interface, the command

    vconfig add eth0 104

will create an interface called `eth0.104`. Any ethernet traffic coming into the
machine on `eth0` that is tagged for VLAN 104 will come out of `eth0.104`, with
its VLAN tag stripped off. Any traffic going into `eth0.104` will have a VLAN
tag for 104 added, and then be sent out on `eth0`. `eth0.104` may be deleted
with:

    vconfig rem `eth0.104`

# How does the HaaS use VLANs?

At present, when a network consisting of nodes 0, 1 and 2, and headnode H,
using vlan tag N is deployed,

* The ports to which 0, 1 and 2 are attached are configured for access mode,
  associated with VLAN N.
* An interface `ethM.N` is created on the HaaS master, where `ethM` is a network
  interface connected to the switch. `ethM` must be connected to a port that is
  configured as trunking, with VLAN M being tagged for that port.
* `ethM.N` is attached to H (not directly, see(1)).
* H is started.

From here, we have an isolated network connecting 0, 1, 2 and H. From here,
depending on what is exposed through the nodes' interfaces (e.g. ipmi), H can
manage the nodes.

This setup will need to be adjusted, since we want to allow users to
deploy Openstack onto the nodes, and using VLANs with Neutron is a
common configuration. The fact that tagged traffic would be blocked by
access mode therefore presents a problem. Instead, we probably want to
be using trunked mode, with some number of VLANs tagged. There's a
discussion to be had about how exactly this should look, as well as how
to expose it to the headnode.

(1): The one slight wrinkle with the network setup described above is that libvirt
doesn't actually allow connecting `ethM.N` directly to the VM; instead we
connect both `ethM.N` and the virtualized network interface to a bridge, which
achieves the same effect.
