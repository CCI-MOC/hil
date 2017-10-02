INSTALL
=======

This document describes the installation and setup of HIL on CentOS 7.0.
HIL should work on other distros, but is not well tested or supported.
For development environments, see `Installation - Developers <INSTALL-devel.html>`_.

The HIL Service node
----------------------

This section talks about what must be done on the server upon which HIL runs.

Prerequisite Software
---------------------

HIL requires a number of packages available through the CentOS RPM
repositories, as well as the EPEL repository. EPEL can be enabled via::

    yum install epel-release

Then, the rest of the packages can be installed via::

    yum install libvirt bridge-utils ipmitool telnet httpd mod_wsgi python-pip qemu-kvm python-virtinst virt-install python-psycopg2 vconfig net-tools

In addition, HIL depends on a number of python libraries. Many of these are
available as RPMs as well, but we recommend installing them with pip, since
this will install the versions that HIL has been tested with.  This is done
automatically by the instructions below.


Disable SELinux
---------------

The setup described in this document runs into problems with SELinux. In the
future, we hope to ship a set of SELinux security policies with HIL, but for
now the solution is to disable SELinux::

    sudo setenforce 0

Make sure SELinux is also disabled on startup. To do this `on
CentOS/RHEL <https://wiki.centos.org/HowTos/SELinux>`_, edit
`/etc/selinux/config` to change:
```
SELINUX=enforcing
```
to
```
SELINUX=permissive
```

User need to choose appropriate values for their environment:
-------------------------------------------------------------

For simplicity we have provided default values:
Copy the following lines in file ``hil_env``

        HIL_USER=hil

        HIL_DB_ROLE=hil

        HIL_DB_PASSWORD=secret

        HIL_ADMIN=hil

        HIL_ADMIN_PASSWORD=secret

        HIL_HOME_DIR=/var/lib/hil



Before starting this procedure do::

        source hil_env


Setting up system user for HIL:
--------------------------------

First create a system user ``${HIL_USER}`` with::

  sudo useradd --system ${HIL_USER} -d /var/lib/hil -m -r


The HIL software itself can then be installed as root by running::

    sudo su -
    cd /root
    git clone https://github.com/CCI-MOC/hil
    cd hil
    sudo python setup.py install


hil.cfg
--------

HIL is configured with ``hil.cfg``. This file contains settings for both the
CLI client and the server. If ``hil.cfg`` is not found, hil would refuse to run
and exit. Carefully read the ``hil.cfg*`` files in ``examples/``,
to understand and correctly set all of the options.  In particular,
the following two fields in the ``headnode`` section are very
important: ``trunk_nic`` must match your choice of trunk NIC in the "Networking
- Bridges" instructions below; ``base_imgs`` must match the name of the base
headnode libvirt instance created in the "Libvirt" instructions below.

For a detailed description of the configuration needed for various switch
setups, see `Network Drivers <network-drivers.html>`_.

Logging level and directory can be set in the ``[general]`` section. For more
information view `logging <logging.html>`_.


``hil.cfg`` file contains sensitive administrative information and should not be exposed to clients or
end users. Therefore, after placing the file at ``/etc/hil.cfg`` its
permissions should be set to read-only and ownership set to ``${HIL_USER}``
From source directory of hil as user root do the following::

    (from /root/hil)
    cp examples/hil.cfg /etc/hil.cfg
    chown ${HIL_USER}:${HIL_USER} hil.cfg
    chmod 400 hil.cfg
    (run following command as ${HIL_USER} from ${HIL_HOME_DIR}
    su - ${HIL_USER}
    ln -s /etc/hil.cfg .

Authentication and Authorization
--------------------------------

HIL includes a pluggable architecture for authentication and authorization.
HIL ships with two authentication backends. One uses HTTP basic auth, with
usernames and passwords stored in the hil database. The other is a "null"
backend, which does no authentication or authorization checks. This can be
useful for testing and experimentation but *should not* be used in production.
You must enable exactly one auth backend.

In productions system where non-null backend is active, end users will have to include
a username and password as additional parameters in ``client_env`` file to be able to
communicate with the hil server. This is user/password should be registered with the
hil auth backend using hil.


Database Backend
^^^^^^^^^^^^^^^^

To enable the database backend, make sure the **[extensions]** section of
``hil.cfg`` contains::

  hil.ext.auth.database =

Keystone Backend
^^^^^^^^^^^^^^^^

To enable the Keystone backend, make sure the **[extensions]** section of
``hil.cfg`` contains::

  hil.ext.auth.keystone =

Visit the `Keystone configuration guide <keystone-auth.html>`_ for more information.

Null Backend
^^^^^^^^^^^^

To enable the null backend, make sure **[extensions]** contains::

  hil.ext.auth.null =

Setting Up HIL Database
------------------------

The only DBMS currently supported for production use is PostgreSQL.
(SQLite is supported for development purposes *only*).
There are many ways of setting up PostgreSQL server.
`Install configure PostgreSQL CENTOS7 <Install_configure_PostgreSQL_CENTOS7.html>`_.
provides one way to accomplish this.

To create the database tables, first make sure ``hil.cfg`` is set up the way
you need, including any extensions you plan to use, then::

    sudo -i -u ${HIL_USER}; hil-admin db create

If the authorization backend activated in ``hil.cfg`` is  ``hil.ext.auth.database =``
then you will need to add an initial user with administrative privileges to the
database in order to bootstrap the system.
You can do this by running the following command (as user ``hil``)::

  sudo -i -u ${HIL_USER}; hil create_admin_user ${HIL_ADMIN_USER} ${HIL_ADMIN_PASSWORD}

You can then create additional users via the HTTP API. You may want to
subsequently delete the initial user; this can also be done via the API.



All HIL commands in these instructions should be run in this directory::

  cd /var/lib/hil

Networking - Bridges
--------------------

Currently HIL only supports one mechanism for layer-2 isolation: 802.1q VLANs.
One NIC on the HIL host is designated the "trunk NIC".  All network traffic to
headnode VMs in HIL is routed through this trunk NIC, on a tagged VLAN.  As
such, the port on the switch that this NIC connects to must have all of HIL's
VLANs trunked to it.  Currently, this configuration must be done manually.

HIL uses Linux bridges to route the traffic from the trunk NIC to the
headnodes. Currently the bridges and VLAN NICs for this must be created
ahead of time.  The provided script ``create_bridges`` will create bridges
for all VLANS in the allocation pool. It must be run in the directory that
contains ``hil.cfg``. This pre-allocation is easier to reason about
than on-demand creation, and allows HIL to be run as an unprivileged user,
but it also causes some limitations.  For instance, because of this, headnodes
can only be connected to networks with allocated VLANs.  The bridges must also
be pre-allocated again on each boot. For now, the recommened method is to use
``systemd``.  A ``systemd`` service for running the ``create_bridges`` script is available
in the 'scripts' directory.

Name of the service is: ``create_bridges.service``

Name of the script is: ``create_bridges``

Centos:
^^^^^^^

Centos uses systemd to controll all its processes.

Place the file ``create_bridges.service`` under:
``/usr/lib/systemd/system/``

Ubuntu:
^^^^^^^
Systemd is available from Ubuntu 15.04 onwards and LTS version 16.04 will ship with systemd by default.

Edit the ``create_bridges.service`` file and change the ExecStart
to
``/usr/local/bin/create_bridges``

Place the file ``create_bridges.service`` under:
``/lib/systemd/system/``

Starting the service:
^^^^^^^^^^^^^^^^^^^^^

Following commands will start the daemon:
``systemctl daemon-reload``
``systemctl start create_bridges.service``

You can check the status using:
``systemctl status create_bridges.service``

To auto-start the service on boot (recommended):
``systemctl enable create_bridges.service``

For systems that do not support systemd:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can add the following line::

  (cd /etc && create_bridges)

to the end of ``/etc/rc.local``.

You can also run the this command manually as root user to create the bridges.

HIL must additionally have IP connectivity to the switch's administration
console.  Right now the only mechanism for connecting to the switch is via
telnet (with `plans <https://github.com/CCI-MOC/hil/issues/46>`_ to support
ssh). As such, the administration console should only be accessible through a
trusted private network.

Libvirt
-------

We must reconfigure ``libvirt`` to allow (some) unprivileged users access to
the system QEMU session.  To do this, edit ``/etc/libvirt/libvirtd.conf`` and
uncomment the following lines::

  unix_sock_group = "libvirt"
  auth_unix_ro = "none"
  auth_unix_rw = "none"

Then create the group 'libvirt' and add the HIL user to that group::

  sudo groupadd libvirt
  sudo gpasswd libvirt -a hil

Finally, restart ``libvirt`` with::

  sudo service libvirtd restart

You should also set libvirt to start on boot::

  sudo chkconfig libvirtd on

Headnode image
^^^^^^^^^^^^^^
Now we must make a clonable base headnode.  (One is required, and more are
allowed.)  First create a storage pool.  Any kind can be used, but we will only
document creating a directory-backed storage pool::

  virsh --connect qemu:///system pool-define pool.xml

where ``pool.xml`` contains a description of the pool::

  <pool type="dir">
    <name>hil_headnodes</name>
    <target>
      <path>/var/lib/libvirt/images</path>
    </target>
  </pool>

The directory specified by path must already exist, and be readable and
writable by the ``libvirt`` user. Then activate the pool, and make the it
activate on boot, with::

  virsh --connect qemu:///system pool-start hil_headnodes
  virsh --connect qemu:///system pool-autostart hil_headnodes

The scripts in ``examples/cloud-img-with-passwd`` can be used to build
an ubuntu 14.04 or centos 7 disk image with a default root password. Read
the README in that directory for more information.

Once the disk image is built, copy ito the storage pool directory (here we
assume it is called ``base.img``)::

  mv base.img /var/lib/libvirt/images/

Finally, create the base headnode with::

  virsh --connect qemu:///system define base.xml

where ``base.xml`` contains a description of the headnode::

  <domain type='kvm'>
    <name>base</name>
    <memory>524288</memory>
    <os>
      <type arch='x86_64'>hvm</type>
      <boot dev='hd'/>
    </os>
    <features>
      <acpi/><apic/><pae/>
    </features>
    <clock offset="utc"/>
    <on_poweroff>destroy</on_poweroff>
    <on_reboot>restart</on_reboot>
    <on_crash>restart</on_crash>
    <vcpu>1</vcpu>
    <devices>
      <emulator>/usr/libexec/qemu-kvm</emulator>
      <disk type='file' device='disk'>
        <driver name='qemu' type='raw'/>
        <source file='/var/lib/libvirt/images/base.img'/>
        <target dev='vda' bus='virtio'/>
      </disk>
      <interface type='network'>
        <source network='default'/>
        <model type='virtio'/>
      </interface>
      <input type='tablet' bus='usb'/>
      <graphics type='vnc'/>
      <console type='pty'/>
      <sound model='ac97'/>
      <video>
        <model type='cirrus'/>
      </video>
    </devices>
  </domain>

Note that the above specifies the format of the disk image as ``raw``; if
you're using an image in another format (such as ``qcow``) you will have
to adjust this.

Many of these fields are probably not needed, but we have not thouroughly
tested which ones. Furthermore, this set of XML duplicates the path to
storage directory; this seems unnecessary.

Users may find the scripts in ``examples/puppet_headnode`` useful for
configuring the ubuntu headnode to act as a PXE server; see the README in
that directory for more information.


Running the Server under Apache
-------------------------------

HIL consists of two services: an API server and a networking server. The
former is a WSGI application, which we recommend running with Apache's
``mod_wsgi``. Create a file ``/etc/httpd/conf.d/wsgi.conf``, with the contents::

  LoadModule wsgi_module modules/mod_wsgi.so
  WSGISocketPrefix run/wsgi

  <VirtualHost 127.0.0.1:80 [::1]:80>
    ServerName 127.0.0.1
    AllowEncodedSlashes On
    WSGIPassAuthorization On
    WSGIDaemonProcess hil user=hil group=hil threads=2
    WSGIScriptAlias / /var/www/hil/hil.wsgi
    <Directory /var/www/hil>
      WSGIProcessGroup hil
      WSGIApplicationGroup %{GLOBAL}
      Order deny,allow
      Allow from all
    </Directory>
  </VirtualHost>

(The file may already exist, with just the ``LoadModule`` option. If so, it is
safe to replace it.)

**Note:** if accessing HIL through a public IP address, be sure to change the ``VirtualHost`` entry accordingly. `VirtualHost documentation <https://httpd.apache.org/docs/current/mod/core.html#virtualhost>`_

**Note:** certain calls to HIL such as *port_register()* may pass arbitrary
strings that should be escaped (see `issue 361 <https://github.com/CCI-MOC/hil/issues/360>`_). By default, Apache `Doesn't
allow <https://stackoverflow.com/questions/4390436/need-to-allow-encoded-slashes-on-apache>`_
this due to security concerns. ``AllowEncodedSlashes On`` enables the passing
of these arguments.

**Note:** For apache to be able to pass the authentication headers to HIL
following directive will have to be turned on

``WSGIPassAuthorization On``

(see http://stackoverflow.com/questions/20940651/how-to-access-apache-basic-authentication-user-in-flask )

If you haven't already, create the directory that will contain the HIL WSGI module::

 sudo mkdir /var/www/hil/

Copy the file ``hil.wsgi`` from the top of the hil source tree to the
location indicated by the ``WSGIScriptAlias`` option. The virtual host and
server name should be set according to the hostname (and port) by which clients
will access the api. Then, restart Apache::

  sudo service httpd restart

You should also set apache to start on boot::

  sudo chkconfig httpd on

Running the network server:
---------------------------

Using systemd:
--------------

A systemd script for running the network server is available in the 'scripts' directory.
Name of the script is: hil_network.service

Centos:
-------

Centos uses systemd to controll all its processes.

Place the file hil_network.service under:
``/usr/lib/systemd/system/``

Ubuntu:
-------
Systemd is available from Ubuntu 15.04 onwards and LTS version 16.04 will ship with systemd by default.

Place the file hil_network.service under:
``/lib/systemd/system/``


Starting the service:
---------------------

Following commands will start the daemon:
``systemctl daemon-reload``
``systemctl start hil_network``

You can check the status using:
``systemctl status hil_network``

To auto-start the service on boot:
``systemctl enable hil_network``


For systems that do not support systemd:
----------------------------------------
Some systems like the LTS version of Ubuntu, Ubuntu 14.04 does not come with systemd pre-installed.
It uses "Upstart" an equivalent of systemd to manage its daemons/processes.

For such systems, the networking server may be started as the HIL user by running::

  hil serve_networks &

To make this happen on boot, add the following to ``/etc/rc.local``::

  (cd /var/lib/hil && su hil -c 'hil serve_networks') &


HIL Client:
------------

If your authentication backend is null, you only need to have the ``HIL_ENDPOINT`` defined
in the ``client_env``. In productions system where non-null backend is active,
end users will have to include a username and password as additional parameters in ``client_env``
file to be able to communicate with the hil server.
If you created a admin user for hil as a part of `Setting Up HIL Database` step,
you will have to pass those credentials to HIL to be able to access, change state of HIL.
Create a file ``client_env`` with following entries::

    export HIL_ENDPOINT=http://127.0.0.1/
    export HIL_USERNAME=<hil_admin_username>
    export HIL_PASSWORD=<hil_admin_password>

To get started with HIL from your home dir do the following::

    source client_env
    hil list_nodes all

If you get an empty list ``[]`` as output then congratulations !!
At this point, you should have a functional HIL service running!

Describe datacenter resources
------------------------------

For HIL to do anything useful, you must use the HIL API to populate the
database with information about the resources in your datacenter -- chiefly
nodes, their NICs and the ports to which those NICs are attached. These are
the relevant API calls:

- ``node_register``
- ``node_delete``
- ``node_register_nic``
- ``node_delete_nic``
- ``port_register``
- ``port_delete``
- ``port_connect_nic``
- ``port_detach_nic``


