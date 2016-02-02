The first time you start working in the repository, set up a clean test
environment (Before you start make sure that you have setup a database 
to be used by for HaaS. HaaS supports SQLIte and PostgreSQL databases. 
You should setup either of the two before you start further. Details to 
setup a database can be found in INSTALL.rst)::

  virtualenv .venv

Next, each time you start working, enter the environment::

  source .venv/bin/activate

Then, proceed with installing the HaaS and its dependencies into the virtual
environment::

  pip install -e .

On systems with older versions of ``pip``, such as Debian Wheezy and Ubuntu
12.04, this install will fail with the following error::

  AttributeError: 'NoneType' object has no attribute 'skip_requirements_regex'

Fix this by upgrading ``pip`` within the virtual environment::

  pip install --upgrade pip

Versions of python prior to 2.7 don't have importlib as part of their
standard library, but it is possible to install it separately. If you're
using python 2.6 (which is what is available on CentOS 6, for example),
you may need to run::

  pip install importlib

You may get an error 'psycopg2 package not found' when you do 'haas init_db' 
in the next step if you are using PostgreSQL database. You may need to run::

  pip install psycopg2

`Testing.md <docs/testing.md>`_ contains more information about testing HaaS.

Configuring HaaS
================

Now the ``haas`` executable should be in your path.  First, create a
configuration file ``haas.cfg``. There are two examples for you to work from,
``examples/haas.cfg.dev-example``, which is oriented towards development, and
``examples/haas.cfg.example`` which is more production oriented.  These config
files are well commented; read them carefully. 

HaaS can be configured to not perform state-changing operations on nodes,
headnodes and networks, allowing developers to run and test parts of a haas
server without requiring physical hardware. To supress actual node and headnode
operations, set ``dry_run = True`` in the ``[devel]`` section. For supressing
actual network switch operations, use the ``mock`` switch driver.

Next initialize the database with the required tables, with ``haas init_db``.

Running HaaS using systemd
==========================

For a short testing simply running the server with ``haas serve`` and ``haas serve_networks`` in separate
terminals should suffice. 

For extensive testing, it is recomended to let systemd manage the processes. 
Sample scripts for managing haas server and its network server is provided under 'scripts' folder.
dev_haas.service manages the haas_server for your development enviornment
dev_haas_network.service manages the network_server for haas for your development enviornment

Ubuntu:
-------

LTS version of Ubuntu, Ubuntu 14.04 does not come with systemd pre-installed.
It uses "Upstart" an equivalent of systemd to manage its daemons/processes.

Systemd is available from Ubuntu 15.04 onwards and LTS version 16.04 will ship with systemd by default.

If you are using Ubuntu with any version prior to 15.04, you will have to install systemd before your can use the scripts provided here.

Instructions on how to modify the file to suit your enviornment are included in the file.
After adjusting the parameters place both the files in
/lib/systemd/system (using sudo)

WARNING: Since systemd is not optimized the way Upstart has been for Ubuntu, you may experience some delay in booting up and shutting down your server after switching to systemd.

Following commands will initialize and enable the services.

systemctl daemon-reload
systemctl start dev_haas
systemctl start dev_haas_network

To start the service on boot do the following:

systemctl enable dev_haas  
systemctl enable dev_haas_network


Centos:
-------
 
On Centos systemd is the default way of managing processes.


Instructions on how to modify the file to suit your enviornment are included in the file.
After adjusting the parameters place both the files in
/usr/lib/systemd/system (using sudo)

Following commands will initialize and enable the services.

systemctl daemon-reload
systemctl start dev_haas
systemctl start dev_haas_network

To start the service on boot do the following:

systemctl enable dev_haas  
systemctl enable dev_haas_network


Almost done:
============

Finally, ``haas help`` lists the various API commands one can use.
Here is an example session, testing ``headnode_delete_hnic``::

  haas project_create proj
  haas headnode_create hn proj
  haas headnode_create_hnic hn hn-eth0
  haas headnode_delete_hnic hn hn-eth0

Additionally, before each commit, run the automated test suite with ``py.test
tests/unit``. If at all possible, run the deployment tests as well (``py.test
tests/deployment``), but this requires access to a sepcialized setup, so if the
patch is sufficiently unintrusive it may be acceptable to skip this step.
