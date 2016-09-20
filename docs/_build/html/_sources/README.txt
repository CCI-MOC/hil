HaaS
========

HaaS is a low-level tool for reserving physical machines and connecting
them via isolated networks. It does not prescribe a particular
method for imaging/managing said machines, allowing the user to use
any solution of their choosing.

HaaS keeps track of available resources in a database, which a system
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
============

Required software/hardware for running a production HaaS include:

* Network switches:

  * At least one switch from the Cisco Nexus 5xxx or Dell PowerConnect 55xx families
  * For environments including more than one switch, all VLANs must be trunked to all managed switches

* A single node that has the following:

  * A webserver capable of supporting the WSGI standard (Apache/mod_wsgi is the only one tested)
  * python 2.7, with the ability to install packages via pip
  * Access to:

    * The Internet or intranet (a way for users to connect to the HaaS service)
    * The administrative telnet IP on the managed switches

  * Currently only CentOS and RHEL 7.x have been tested, though any node that otherwise meets these requirements should function.

* Database: a Postgres database server. Sqlite works but is not recommended for production.

For IPMI proxy functionality:

* Network access from the HaaS service node to the IPMI interfaces of node under management
* Nodes that support IPMI v2+
* A recent version of ipmitool installed on the HaaS service node

For headnode functionality:

* A recent Linux version for the HaaS service node that has libvirt with KVM installed
* Some number of VM templates
* A trunk port connected between the switch and HaaS service node that carries all VLANs accessible from HaaS

Documentation
=============

* `overview.md <docs/overview.md>`_ gives a sense as to how HaaS operates
* `INSTALL.rst <docs/INSTALL.rst>`_ for details on setting up HaaS
* `UPGRADING.rst <docs/UPGRADING.rst>`_ for details on upgrading to a new version of HaaS
* `using.rst <docs/USING.rst>`_ for details on using HaaS as a client
* `apidesc.md <docs/apidesc.md>`_ describes the API at a conceptual level (enough to use it via the ``haas`` command line tool)
* `rest_api.md <docs/rest_api.md>`_ provides a detailed mapping of that API to http requests.
* `developer-guidelines.md <docs/developer-guidelines.md>`_ discusses our code submission and approval process.
* `examples <examples/>`_ contains examples of config files, templates for creating headnode VM images and a script to register nodes with HaaS.
* `The docs directory <docs/>`_ contains assorted other documentation

Please note that the documentation is a mix of Markdown and reStructured Text,
since the latter is preferred by the python and OpenStack communities and the
former was what was originally used.

Mass Open Cloud
===============

This project is part of the larger `Massachusetts Open Cloud
<http://www.massopencloud.org>`_. For a description of the team and other
information, see
`<https://github.com/CCI-MOC/moc-public/blob/master/README.md>`_.

