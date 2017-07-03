# Deployment

This is a guide to the best practices for deploying Hardware Isolation
Layer (HIL).  It documents many of the assumptions that the HIL
development team made in terms of how HIL would be used, how it would be
deployed, and the configuration of the hardware systems it would be
managing.

For instructions on installing HIL, take a look at [Installation](INSTALL.html).
For a general overview, please take a look at [Introduction](README.html).

## Nodes
### BIOS/Firmware

We recommend coming up with a standard list of BIOS settings for your nodes and
documenting them. These could vary between pools of different types, like
virtualization based (which could benefit more from hyperthreading) vs HPC
(which might not).

Settings useful to document would include:

* BIOS boot order
* Hyperthreading
* Whether turbo boosting is enabled

#### Boot order

A provider should consistently set up all nodes to have the same order. It is
recommended that this order consist of: cdrom, disk, PXE. By placing
CDROM first, the datacenter administrator can easily boot the system locally in
order to perform maintenance tasks like upgrading the BIOS.  Having disk come
before PXE allows customers who install an OS to have it boot first, reducing
boot times and avoiding accidental overwriting of their installed OS.

* Note: In the future, we anticipate a feature (see [issue
303](https://github.com/CCI-MOC/hil/issues/303)) where customers can
explicitly request PXE booting for the next boot via an API call, however the
permanent boot order would not likely be able to be changed as that is not
supported by IPMI in a standard way.

#### Devices

For higher security, it may be desirable to disable CD/DVD access to the OS,
only enabling it when needed for maintenance or other reasons. This is because
an inadvertent CD/DVD left in the drive could allow a user to burn an image.
Placed in another system or left in the tray, this image could then allow an
attack on another system.

#### Firmware security

End users will have full control your node. If they are not trusted, it is
extremely important to disable firmware update mechanisms before access is
first given to it. The less reachable this is through remote access (ie -
hardware jumpers vs. software settings) the more secure the system should be.

Ideally, hardware that does not trust the user to update firmware should be
used. Examples of this are AMD Seamicro systems as well as HP Moonshot. Short
of that, it is recommended that one lock down the firmware options as much as
possible in case access were ever gained to the boot screens or IPMI interface.
This includes setting a BIOS menu password as well as disabling any kind of
privileged access from within the OS.

Firmware updates for the motherboard and for peripheral devices should be
disabled via hardware (ideally) or software mechanisms, as they could represent
a vector by which a user (whether maliciously or unintentionally) could impact
future users of a machine and possibly violate their security. It is important
to note that administrators should also monitor the manufacturers' websites for
legitimate firmware upgrades and should regularly update nodes themselves, as
these could contain security or other fixes. Here is an incomplete list of
firmwares to which these guidelines apply:

* BIOS Should be configured *not* to allow updates from within the OS, since
even the root user is untrusted.
* Hard disks
* Network cards
* GPUs
* Other peripherals

## Networks

### Switch configuration
In order to deploy HIL, at least one switch supported by one of HIL's
drivers is required.

This currently includes:

* Dell Powerconnect
* Cisco Nexus 3500 & 5500 (other nexus switches may work as well, but
  are untested)

``null`` and ``mock`` drivers are also included for testing and
experimentation.

### VLANs

The network administrator will need to pre-allocate a set of VLANs to
dedicate to HIL's management. These are kept within the *vlan* section
of the config file.

### Headnodes

Currently, the system or systems that run the HIL service (sometimes
informally called the HIL master) also run the Headnode virtual machines.
These can be used to access and administrate user networks, whether public or
private. To facilitate this, all VLANs that are allocatable by HIL must be
trunked using 802.1Q to HIL service systems. This port upon which these
networks are shared is indicated using the *trunk_nic* member of the
**[headnode]** section.

### Multiple Switches
HIL supports networks spanning multiple switches via 2 mechanisms:

1. Vendor-specific "stacking" features that make all of the switches appear to
   be one big one.
2. By running a network cable between the two switches, and setting all
   VLANs belonging to HIL to be trunked (tagged) on the interfaces
   connecting those switches.

IMPORTANT: If you're operating a multi-switch deployment using technique (2)
above, you should be  sure to configure the switches to prevent VLAN hopping
attacks::

    https://en.wikipedia.org/wiki/VLAN_hopping
