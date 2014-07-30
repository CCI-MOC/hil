# HaaS Architecture Overview

The HaaS (Hardware as a Service) is a tool used to perform network
isolation of physical machines, so that different parties can be
given physical capacity within the same data center, without needing
to trust each other.

## Operation

From a user's perspective, the HaaS allows one to:

* allocate physical nodes
* create login/management nodes (sometimes called headnodes)
* configure networks, in particular:
  * create logical networks
  * connect physical nodes to those logical networks (on a per-nic basis)
* connect login/management nodes to those networks.

Once everything is configured as desired, the user "applies" the
configuration, at which point the necessary adjustments will be made
to the switch (see below), and the login node will boot.

Right now, we're using 802.1q VLANs to achieve network isolation. The
HaaS communicates with a managed switch, to which the physical
hardware is attached. When an "apply" operation is performed, the
HaaS sends commands to the switch which configure the relevant ports
as needed to create the logical networks.

## Anatomy of a Running Installation


                              SWITCH
                           _____________
      <ipmi-nic>-----------] access{N} |
    =node-1=               |           |
      <primary-nic>--------]           |
                           |           |
                           |           |             (                                      )
                           |           |             (    ^br-vlanM^------^trunk-nic.M^     )
      <ipmi-nic>-----------] access{M} |             ( %hn-B%                               )
    =node-2=               |           |             (                                      )
      <primary-nic>--------]           |             ( %hn-A%                               )
                           |           |             (    ^br-vlanN^------^trunk-nic.N^     )
                           |           |             (                                      )
                           |           |             (                                      )
      <ipmi-nic>-----------]     trunk [--------<trunk-nic>=haas-master=
    =node-3=               |           |
      <primary-nic>--------]___________[

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


A typical installation of the HaaS will have the following components:

* One machine which acts as the "HaaS master". This machine will be
  running the HaaS api server itself.
* A managed switch
* One or more physical nodes, each of which may have one or more network
  interfaces.

These components will be configured as follows:

* All of the physical nodes will have some subset (possibly all) of
  their nics connected to the managed switch.
  * The ports that these are connected to will be set to access mode.
* The HaaS master will have one nic connected to the managed switch.
  * The corresponding port will be set to trunk mode, with all vlans
    enabled.
* The HaaS master will be running the libvirt daemon, which will have at
  least one VM, powered off, called "base-headnode", which can be cloned
  and started to provide login/management nodes.
* A network object in the HaaS corresponds to a vlan id. When a network
  is applied, the following will occur:
  * All ports connected corresponding nics on the logical network will
    have their access vlan set to the vlan id associated with the
    network.
  * On the HaaS master, a vlan'd nic (e.g. eth0.104, given that eth0 is
    connected to the trunked port) will be created, and the
    corresponding nic on the virtual machine will be connected to it
    * The vm's nic is connected indirectly, through a bridge device;
      libvirt is unable to attach directly to physcal nics. This is an
      implementation detail, but worth knowing.
