INSTALL-devel
=============

Following guide covers setting up a developement environment for HIL
on a CentOS/RHEL based system.

Dependencies:
-------------
There are a few things that HIL expects the operating system to have::

  yum install epel-release bridge-utils  gcc  httpd  ipmitool libvirt \
  libxml2-devel  libxslt-devel  mod_wsgi net-tools python-pip python-psycopg2 \
  python-virtinst python-virtualenv qemu-kvm telnet vconfig virt-install

HIL requires a database server and currently supports only SQLite and PostgreSQL.
If you choose to use PostgreSQL database it is recommended to create a new system user
with a separate home directory. This user will be configured to control the hil database.
The development environment will be created in its home directory.

Setting PostgreSQL for development environment:
------------------------------------------------

If you choose to use sqlite database, skip this section and go to `Getting Started with HIL Installation`_.

For setting up PostgreSQL, you will have to install the requisite packages on your system.
Make sure your account can `sudo` to execute the following commands.

Part 1: Install PostgreSQL server.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Initialize the system. Configure PostgreSQL to allow password authentication.

Install the requisite packages on your server::

  sudo yum install postgresql-server postgresql-contrib -y


Initialize postgresql::

  sudo postgresql-setup initdb


Replace the term **ident** from following lines in file
**/var/lib/pgsql/data/pg_hba.conf** with **md5**.

Before::

  # "krb5", "ident", "peer", "pam", "ldap", "radius" or "cert".  Note that
  host    all             all             127.0.0.1/32            ident
  host    all             all             ::1/128                 ident
  #host    replication     postgres        127.0.0.1/32            ident
  #host    replication     postgres        ::1/128                 ident

After::

  # "krb5", "ident", "peer", "pam", "ldap", "radius" or "cert".  Note that
  host    all             all             127.0.0.1/32            md5
  host    all             all             ::1/128                 md5
  #host    replication     postgres        127.0.0.1/32            ident
  #host    replication     postgres        ::1/128                 ident


Start postgresql service::

  $ sudo systemctl start postgresql
  $ sudo systemctl enable postgresql


Part 2: Create a system user, database and database role.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Setting up development environment with PostgreSQL backend becomes
easy with a dedicated user controlling the database as well as the
development environment.

Let that username be `hil_dev`.
For simplicity we will use the same name for database and database role.

Create a new user on your system::

  useradd --system -m -d /home/hil_dev -s /bin/bash -c "for HIL development" hil_dev

This will create a `hil_dev` user with following attributes::

  hil_dev:x:1002:1002:for HIL development:/home/hil_dev:/bin/bash

exact uid/gid may vary depending on your system.

Switch to the `hil_dev` user::

  sudo -u hil_dev -i

Setup database and role to control it.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create database named `hil_dev` owned by user also named as `hil_dev`.

1. Create a database role named `hil_dev` with privileges to::

   -r create roles
   -d create databases and
   -P will prompt for the password of the new user.

This is necessary since we have configured PostgreSQL to use password authentication::

   sudo -i -u postgres
   $ createuser -r -d -P hil_dev
   Enter password for new role:  <Input password for database role hil>
   Enter it again: <Retype password for role hil>


Confirm that the role with requisite privileges is created **as postgres user**::

  $ psql -c '\dg'
                             List of roles
   Role name |                   Attributes                   | Member of
  -----------+------------------------------------------------+-----------
   hil_dev   | Create role, Create DB                         | {}
   postgres  | Superuser, Create role, Create DB, Replication | {}


If you wish to delete the user. do the following **as postgres user**::

  dropuser hil_dev

**Note**: Make sure that the database role you create corresponds to an existing system user.
eg. There has to be a system user `hil` to access database named `hil` as database role named `hil`.


Create database `hil_dev` owned by database role `hil_dev`::

  sudo -i -u hil_dev
  $ createdb hil

Confirm it created a database named `hil_dev` and it is owned by `hil_dev`::


  $ psql -c '\l'
                                  List of databases
    Name     |  Owner   | Encoding |   Collate   |    Ctype    |   Access privileges
  -----------+----------+----------+-------------+-------------+-----------------------
   hil_dev   | hil_dev  | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
   postgres  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
   template0 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
             |          |          |             |             | postgres=CTc/postgres
   template1 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
             |          |          |             |             | postgres=CTc/postgres


switch to user `hil_dev`.
All subsequent installation steps assumes you are in the
home directory of `hil_dev`


Getting Started with HIL Installation
---------------------------------------
First you will need to fork and clone the HIL repo into your dev VM.::

  git clone https://github.com/**username**/hil
  cd hil


The first time you start working in the repository, set up a clean test
environment::

  virtualenv .venv

Enter the environment (do this every time you start working with HIL dev environment)::

  source .venv/bin/activate

Then, proceed with installing the HIL and its dependencies into the virtual
environment::

  pip install -e .[tests]

The ``[tests]`` part pulls in dependencies only needed for running the test
suite. There are several other "extras" you can specify, which pull in
dependencies needed for optional HIL features:

* ``postgres`` to use a PostgreSQL database.
* ``keystone-auth-backend`` for the keystone auth backend.
* ``keystone-client`` for keystone support in the client library and command
  line tool.


For older systems:
------------------

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
-------------------------
The default dev environment uses SQLite as a database, so if you're using it you can skip this section.

If you wish to use PostgreSQL instead, you may get an error ``psycopg2 package not found``,
when you do ``hil-admin db create`` in the next step.
To avoid that problem, you may need to install some packages based on your system type:

CentOS::

  sudo yum install postgresql-devel

Ubuntu::

  sudo apt-get install libpq-dev

After these packages have been installed, you'll then need the python postgres
driver in your HIL virtualenv::

  pip install -e .[postgres]


Configuring HIL
-----------------

Now the ``hil`` executable should be in your path. First, create a
configuration file ``hil.cfg`` because if it's not found then hil would refuse
to run and exit. There are two examples for you to work from,
``examples/hil.cfg.dev-no-hardware``, which is oriented towards development,
and ``examples/hil.cfg`` which is more production oriented. These config files
are well commented; read them carefully.

HIL can be configured using ``hil.cfg`` to not perform state-changing
operations on nodes, headnodes and networks, allowing developers to run and
test parts of a hil server without requiring physical hardware. To suppress
actual node and headnode operations, set ``dry_run = True`` in the ``[devel]``
section.


If using PostgreSQL as a database backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you choose to use PostgreSQL and did the necessary steps as described above,
put following string in **hil.cfg** under section **[database]**::

  uri = postgresql://hil_dev:<clear text password>@localhost:5432/hil_dev


It follows the format: `postgresql://<user>:<password>@<address>/<dbname>`
where ``<user>`` is the name of the postgres user you created, ``<password>`` is
its password, ``<dbname>`` is the name of the database you created, and
``<address>`` is the address which hil should use to connect to postgres (In a
typical default postgres setup, the right value is ``localhost``).

Setting up extensions
----------------------

Most customizations require including extension names within the ``[extensions]``
section.

For suppressing actual network switch operations, use the ``mock`` switch driver ::
  hil.ext.switches.mock =

To suppress actual IPMI calls made to nodes on account of node_power_cycle
requests, enable the ``mock`` OBM driver with ::

  hil.ext.obm.mock =

You can choose to disable authentication mechanism by enabling the ``null``
auth driver ::

  hil.ext.auth.null =

Database auth
-------------

To enable an authentication mechanism, an appropriate authentication backend
will need to be selected and enabled. Note that auth backends are mutually
exclusive. For the database method (which stores users/passwords in the DB),
add ::

  hil.ext.auth.database =


Next initialize the database with the required tables::

  hil-admin db create

Start the server
-----------------

Run the server with the port number as defined in ``hil.cfg``::

  hil serve <port no>

and in a separate window terminal::

  hil serve_networks

Finally, ``hil help`` lists the various API commands one can use.
Here is an example session, testing ``headnode_delete_hnic``::

  hil project_create proj
  hil headnode_create hn proj img1
  hil headnode_create_hnic hn hn-eth0
  hil headnode_delete_hnic hn hn-eth0

Testing
-------

Additionally, before each commit, run the automated test suite with ``py.test
tests/unit``. If at all possible, run the deployment tests as well (``py.test
tests/deployment``), but this requires access to a specialized setup, so if the
patch is sufficiently unintrusive it may be acceptable to skip this step.

`Testing <testing.html>`_ contains more information about testing HIL.
`Migrations <migrations.html>`_ dicsusses working with database migrations
and schema changes.
