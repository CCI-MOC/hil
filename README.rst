**HaaS**
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
- create isolated logical networks
- create "headnodes," which are small virtual machines usable for
  management/provisioning purposes
- connect network interfaces belonging to physical and/or headnodes to
  logical networks.

**A typical user workflow might look like:**

1. Reserve some machines.
#. Create a logical "provisioning" network.
#. Connect each machine's IPMI controller to said network.
#. Create a headnode, and attach it to the provisioning network
#. Log in to the headnode, and use IPMI to deploy some image/operating
   system onto the nodes.

This is only an example; mechanisms other than IPMI could be used
for power cycling, booting, and provisioning machines.

HaaS is still in a very early alpha stage of development, and isn't
production ready yet.

**Hacking**
===========

This project is part of the larger Massachusetts Open Cloud, for list
of authors, description of the team, workflow, ... look here_  

There's some assorted documentation in the `doc/` directory.

.. _here: https://github.com/CCI-MOC/moc-public/blob/master/README.md

**Getting Started**
===================


The first time you start working in the repository, set up a clean test
environment::

  virtualenv .venv

Next, each time you start working, enter the environment::

  source .venv/bin/activate

The first time you enter the environment, install the ``haas`` code and all
its dependencies into the virtual environment::

  pip install -e .

On systems with older versions of ``pip``, such as Debian Wheezy and Ubuntu
12.04, this install will fail with the following error::

  AttributeError: 'NoneType' object has no attribute 'skip_requirements_regex'

Fix this by upgrading ``pip`` within the virtual environment::

  pip install --upgrade pip


**Testing the HaaS**
====================


Now the ``haas`` executable should be in your path.  First, create a
configuration file by copying ``haas.cfg.example`` to ``haas.cfg``, and
editing it as appropriate.  (In particular, if you are testing deployment, you
should read the comments in ``haas.cfg.example`` to see what options are
relevant.)  Then initialize the database with the required tables, with ``haas
init_db``.  Run the server with ``haas serve``.  Finally, see ``haas help``
for the various API commands one can test.  Here is an example session,
testing ``headnode_delete_hnic``::

  haas group_create gp
  haas headnode_create hn gp
  haas headnode_create_hnic hn hn-eth0 DE:AD:BE:EF:20:12
  haas headnode_delete_hnic hn hn-eth0


Additionally, before each commit, run the automated test suite with ``py.test
tests``.  This will do only the most basic level of testing.  For additional
features, including coverage reporting, see ``docs/testing.md``
