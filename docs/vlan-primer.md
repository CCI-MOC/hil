# VLAN Primer

This document is a brief primer on 802.1q VLANs (Virtual LANs): what they are,
how switches tend to deal with them, how Linux deals with them, and how the
HIL uses them.

## Managed vs. Unmanaged Switches

The primary function of an *unmanaged* switch is to connect several
computers into a single network segment. This is similar to the purpose
of a hub - which is in essence just a shared wire - except that it
understand the ethernet protocol and thus does not have to send traffic
to every machine. Instead it can only send traffic to the machines which
need to see it. This improves performance somewhat, but for the most
part does not affect usage of the device.

For a managed switch, the basic purpose is the same. However, a managed
switch provides additional capabilities, and typically can be configured
via a web interface, serial console, or telnet or ssh.

One piece of additional functionality provided by nearly all managed
switches is support for VLANs, which are typically used to create
logical networks within the switch - i.e. they allow the switch to be
divided into isolated sections, which cannot communicate with one
another.

## What are VLANs?

At a most basic level, a VLAN is simply a 12 bit tag in the header of an
ethernet packet, which can be used by networking equipment. Mostly this
is used as described above - it provides both the switch and other
devices with information about which logical network the packet belongs
to.

## How do switches deal with VLANs?

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

## How does Linux deal with VLANs?

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

## How does the HIL use VLANs?

At present, when a network consisting of nodes 0, 1 and 2, and headnode H,
using vlan tag N is deployed,

* The ports to which 0, 1 and 2 are attached are configured for trunked
  mode, and given access to VLAN N. Depending on the user's preferences,
  the VLAN may either be tagged or native, on a per-port basis.
* An interface `ethM.N` is created on the HIL master, where `ethM` is a network
  interface connected to the switch. `ethM` must be connected to a port that is
  configured as trunking, with VLAN M being tagged for that port.
* `ethM.N` is attached to H (not directly, see(1)).
* H is started.

From here, we have an isolated network connecting 0, 1, 2 and H. H can then
manage the nodes by e.g. providing a PXE server and invoking the HIL API to
reboot the nodes.

(1): The one slight wrinkle with the network setup described above is that libvirt
doesn't actually allow connecting `ethM.N` directly to the VM; instead we
connect both `ethM.N` and the virtualized network interface to a bridge, which
achieves the same effect.
