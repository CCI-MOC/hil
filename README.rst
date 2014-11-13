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

Documentation
=============

* `overview.md <docs/overview.md>`_ gives a sense as to how HaaS operates
* `INSTALL.rst <INSTALL.rst>`_ for details on setting up HaaS
* `using.rst <docs/USING.rst>`_ for details on using HaaS as a client 
* `apidesc.md <docs/apidesc.md>`_ describes the API at a conceptual level (enough to use it via the ``haas`` command line tool)
* `rest_api.md <docs/rest_api.md>`_ provides a detailed mapping of that API to http requests.

Please note that some of the documentation is written in Markdown and some in the reStructured Text format preferred by the python and OpenStack communities.

Hacking
===========

This project is part of the larger Massachusetts Open Cloud, for a list
of authors, description of the team, development workflow, etc. see:

https://github.com/CCI-MOC/moc-public/blob/master/README.md

The file ``HACKING.rst`` In this directory describes the technical details
of running HaaS in development.

There is also some assorted documentation in the `doc/` directory.
