The first time you start working in the repository, set up a clean test
environment (Before you start make sure that you have setup a database
to be used by for HaaS. HaaS supports SQLite and PostgreSQL databases.
You should setup either of the two before you start further. Details to
setup a database can be found in INSTALL.rst)::

  virtualenv .venv

Next, each time you start working, enter the environment::

  source .venv/bin/activate

Then, proceed with installing the HaaS and its dependencies into the virtual
environment::

  pip install -e .


For older systems:
==================

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


Setting up the Database:
========================
By default development environment uses SQLite as a database backend.
If you choose to use it, you can skip this section. 

If you wish to use postgreSQL instead, you may get an error 'psycopg2 package not found' 
when you do 'haas-admin db create' in the next step. You may need to install 
following package on your system 

if its Centos::  

  yum install postgresql-devel

if its Ubuntu::
  
  sudo apt-get install libpq-dev

before installing ``psycopg2`` in the virtualenv for HaaS::

  pip install psycopg2

After this follow instructions provided in
`Install_configure_postgreSQL_CENTOS7.md <Install_configure_postgreSQL_CENTOS7.md>`_

Configuring HaaS
================

Now the ``haas`` executable should be in your path.  First, create a
configuration file ``haas.cfg``. There are two examples for you to work from,
``examples/haas.cfg.dev-example``, which is oriented towards development, and
``examples/haas.cfg.example`` which is more production oriented.  These config
files are well commented; read them carefully.

HaaS can be configured to not perform state-changing operations on nodes,
headnodes and networks, allowing developers to run and test parts of a haas
server without requiring physical hardware. To suppress actual node and headnode
operations, set ``dry_run = True`` in the ``[devel]`` section. For suppressing
actual network switch operations, use the ``mock`` switch driver.

Next initialize the database with the required tables, with ``haas-admin db create``.
Run the server with ``haas serve`` and ``haas serve_networks`` in separate
terminals.  Finally, ``haas help`` lists the various API commands one can use.
Here is an example session, testing ``headnode_delete_hnic``::

  haas project_create proj
  haas headnode_create hn proj
  haas headnode_create_hnic hn hn-eth0
  haas headnode_delete_hnic hn hn-eth0

Additionally, before each commit, run the automated test suite with ``py.test
tests/unit``. If at all possible, run the deployment tests as well (``py.test
tests/deployment``), but this requires access to a sepcialized setup, so if the
patch is sufficiently unintrusive it may be acceptable to skip this step.

`testing.md <testing.md>`_ contains more information about testing HaaS.
`migrations.md <migrations.md>`_ dicsusses working with database migrations
and schema changes.
