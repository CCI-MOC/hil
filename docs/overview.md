# HIL Architecture Overview

The HIL (Hardware Isolation Layer) is a tool used to perform network
isolation of physical machines, so that different parties can be
given physical capacity within the same data center, without needing
to trust each other.

## Operation

From a user's perspective, the HIL allows one to:

* allocate physical nodes
* create login/management nodes (sometimes called headnodes)
* configure networks, in particular:
  * create logical networks
  * connect physical nodes to those logical networks (on a per-nic basis)
* connect login/management nodes to those networks.

Right now, we're using 802.1q VLANs to achieve network isolation. The
HIL communicates with a managed switch, to which the physical
hardware is attached. When networking operations are performed, the
HIL sends commands to the switch which configure the relevant ports
as needed to create the logical networks.

## Anatomy of a Running Installation


                              SWITCH
                           _____________
      <nic1>---------------] access{N} |
    =node-1=               |           |
      <nic2>---------------]           |
                           |           |
                           |           |             (                                      )
                           |           |             (    ^br-vlanM^------^trunk-nic.M^     )
      <nic1>---------------] access{M} |             ( %hn-B%                               )
    =node-2=               |           |             (                                      )
      <nic2>---------------]           |             ( %hn-A%                               )
                           |           |             (    ^br-vlanN^------^trunk-nic.N^     )
                           |           |             (                                      )
                           |           |             (                                      )
      <nic1>---------------]     trunk [--------<trunk-nic>=hil-master=
    =node-3=               |           |
      <nic2>---------------]___________[

        Legend:

            ( running in software )
            <physical network interface>
            ^virtual/logical network interface^
            =physical node=
            %virtualized node%
            ]/[ switch's Ethernet ports
            --- connection (virtual or physical)
            access{X} Denotes that the adjacent port is set to access mode, with vlan #X.
            trunk Denotes that the adjacent port is set to trunk mode.


A typical installation of the HIL will have the following components:

* The HIL API server and headnode VM host
* A managed switch
* One or more physical nodes, each of which has one or more network
  interfaces.

These components will be configured as follows:

* All of the physical nodes will have some subset (possibly all) of
  their nics connected to the managed switch.
  * The ports that these are connected to will be set to access mode.
* The HIL headnode host will have one nic connected to the managed switch.
  * The corresponding port will be set to trunk mode, with all vlans
    enabled.
* The HIL master will be running the libvirt daemon, which will have at least
  one VM, powered off, which can be cloned and started to provide
  login/management nodes.
* A network object in the HIL corresponds to a vlan id.  (In future versions,
  we will also allow other mechanisms, such as VXLAN.)  Network operations
  have the following effects
  * Ports added to the network will have their access vlan set to the vlan id
    associated with the network.
  * Ports removed from the network will be set to access no vlans.
