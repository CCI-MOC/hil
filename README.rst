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


First, set up a clean test environment::

  virtualenv .venv

You only need do this once ever, most likely.  (Note that Git will ignore this
directory.)  Next, each time you start working, enter the environment with::

  source .venv/bin/activate

This assumes that you are using the bash shell.  For other shells, see the
other files in the directory ``.venv/bin``. Then, once you are ready to test
the *haas* code, run::

  pip install -e .

Now ``haas`` will be in your path, and you can run it.  However, if you are
running a Debian Wheezy system (among possibly others), you will get the
following error::

  AttributeError: 'NoneType' object has no attribute 'skip_requirements_regex'

To fix this, run::

  pip install --upgrade pip

You only need to do this once.
