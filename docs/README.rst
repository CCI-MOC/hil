HIL - Introduction
====================

HIL is a low-level tool for reserving physical machines and connecting
them via isolated networks. It does not prescribe a particular
method for imaging/managing said machines, allowing the user to use
any solution of their choosing.

HIL keeps track of available resources in a database, which a system
administrator must populate initially.

**This includes information such as:**

- What machines are available
- What network interfaces they have
- Where those NICs are connected (what port on what switch)

**From there, a regular user may:**

- Reserve physical machines
- Create isolated logical networks
- Create "headnodes," which are small virtual machines usable for
  management/provisioning purposes
- Connect network interfaces belonging to physical and/or headnodes to
  logical networks.
- Reboot their machines, view the serial consoles -- aditionaly such management
  features may exist in the future.

**A typical user workflow might look like:**

1. Reserve some machines.
#. Create a logical "provisioning" network.
#. Connect a NIC from each machine to the provisioning network. In particular,
   one could connect a NIC from which the machine will attempt to boot.
#. Create a headnode, and attach it to the provisioning network
#. Log in to the headnode, set up a PXE server, reboot the nodes, and deploy an
   operating system on them via the network.

Requirements
-------------

Required software/hardware for running a production HIL include:

* Network switches:

  * At least one switch from the Cisco Nexus 5xxx or Dell PowerConnect 55xx families
  * For environments including more than one switch, all VLANs must be trunked to all managed switches

* A single node that has the following:

  * A webserver capable of supporting the WSGI standard (Apache/mod_wsgi is the only one tested)
  * python 2.7, with the ability to install packages via pip
  * Access to:

    * The Internet or intranet (a way for users to connect to the HIL service)
    * The administrative telnet IP on the managed switches

  * Currently only CentOS and RHEL 7.x have been tested, though any node that otherwise meets these requirements should function.

* Database: a Postgres database server. Sqlite works but is not recommended for production.

For IPMI proxy functionality
:
* Network access from the HIL service node to the IPMI interfaces of node under management
* Nodes that support IPMI v2+
* A recent version of ipmitool installed on the HIL service node

For headnode functionality:

* A recent Linux version for the HIL service node that has libvirt with KVM installed
* Some number of VM templates
* A trunk port connected between the switch and HIL service node that carries all VLANs accessible from HIL

Documentation
--------------

* The full documentation is availalbe at `ReadTheDocs <http://hil.readthedocs.io/en/latest/>`_ in a beautiful and easy to navigate web interface.
* `The docs directory <https://github.com/CCI-MOC/hil/tree/master/docs>`_ contains all the documentation in .rst and .md format
* `Examples <https://github.com/CCI-MOC/hil/tree/master/examples>`_ contains examples of config files, templates for creating headnode VM images and a script to register nodes with HIL.


Mass Open Cloud
----------------

This project is part of the larger `Massachusetts Open Cloud
<http://www.massopencloud.org>`_. For a description of the team and other
information, see
`<https://github.com/CCI-MOC/moc-public/blob/master/README.md>`_.

