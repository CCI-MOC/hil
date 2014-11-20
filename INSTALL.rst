This document describes the installation and setup of HaaS on CentOS 6.5.
HaaS should work on other distros, but is not well tested or supported.
For development environments, see ``HACKING.rst``.

The HaaS Service node
=====================

This section talks about what must be done on the server upon which HaaS runs.

Prerequisite Software
---------------------

HaaS requires a number of packages available through the CentOS RPM
repositories, as well as the EPEL repository. EPEL can be enabled via:

::

    yum install epel-release

Then, the rest of the packages can be installed via:

::

    yum install libvirt bridge-utils ipmitool telnet sqlite httpd mod_wsgi python-pip qemu-kvm python-virtinst

In addition, HaaS depends on a number of python libraries. Many of these are
available as RPMs as well, but we recommend installing them with pip, since
this will install the versions that HaaS has been tested with.  This is done
automatically by the instructions below.

First, HaaS depends on a utility library called moc-rest. It can be installed
via:

::

    git clone https://github.com/CCI-MOC/moc-rest
    cd moc-rest
    sudo python setup.py install

The HaaS software can then be installed similarly:

::

    git clone https://github.com/CCI-MOC/haas
    cd haas
    sudo python setup.py install

Disable SELinux
---------------

The setup described below runs into problems with SELinux related to the sqlite
database. For now the recommended solution is to simply disable SELinux. In
future releases, we will support and recommend the use of SELinux with another
DBMS, such as MySQL.

::

    sudo setenforce 0

Create User
-----------

First create a system user ``haas_user`` with::

  sudo useradd haas_user -d /var/lib/haas -m -r

haas.cfg
--------

HaaS is configured with two separate ``haas.cfg`` files. One file contains
settings for the CLI client, and the other file contains settings for the
server. Carefully read the files ``haas.cfg.server-example`` and
``haas.cfg.client-example`` (at the top of the source tree), to understand
and correctly set all of the options.  In particular, the following two
fields in the ``headnode`` section of ``haas.cfg.server-example`` are very
important: ``trunk_nic`` must match your choice of trunk NIC in the
"Networking - Bridges" instructions below; ``base_imgs`` must match the name
of the base headnode libvirt instance created in the "Libvirt" instructions
below.

The ``haas.cfg.server-example`` file should be placed at ``/etc/haas.cfg``,
and the ``haas.cfg.server-example`` file should be placed at
``/var/lib/haas/haas.cfg``; The ``haas.wsgi`` script, described below,
requires this.

It's a good idea to set the owner of the file to ``haas_user`` and to set
file permissions such that other users are restricted from reading its
sensitive contents, such as usernames and passwords::

  chown haas_user /etc/haas.cfg
  chmod 600 /etc/haas.cfg

Networking - Bridges
--------------------

Currently HaaS only supports one mechanism for layer-2 isolation: 802.1q VLANs.
One NIC on the HaaS host is designated the "trunk NIC".  All network traffic to
headnode VMs in HaaS is routed through this trunk NIC, on a tagged VLAN.  As
such, the port on the switch that this NIC connects to must have all of HaaS's
VLANs trunked to it.  Currently, this configuration must be done manually.

HaaS uses Linux bridges to route the traffic from the trunk NIC to the
headnodes. Currently the bridges and VLAN NICs for this must be created
ahead of time.  The provided script ``create_bridges`` will create bridges
for all VLANS in the allocation pool. It must be run in the directory that
contains ``haas.cfg``. This pre-allocation is easier to reason about
than on-demand creation, and allows HaaS to be run as an unprivileged user,
but it also causes some limitations.  For instance, because of this, headnodes
can only be connected to networks with allocated VLANs.  The bridges must also
be pre-allocated again on each boot. For now, the recomended approach is to add::

  (cd /etc && create_bridges)

to the end of ``/etc/rc.local``.

HaaS must additionally have IP connectivity to the switch's administration
console.  Right now the only mechanism for connecting to the switch is via
telnet (with `plans <https://github.com/CCI-MOC/haas/issues/46>`_ to support
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

Then create the group 'libvirt' and add the HaaS user to that group::

  sudo groupadd libvirt
  sudo gpasswd libvirt -a haas_user

Finally, restart ``libvirt`` with::

  sudo service libvirtd restart

Headnode image
^^^^^^^^^^^^^^
Now we must make a clonable base headnode.  (One is required, and more are
allowed.)  First create a storage pool.  Any kind can be used, but we will only
document creating a directory-backed storage pool::

  virsh --connect qemu:///system pool-define pool.xml

where ``pool.xml`` contains a description of the pool::

  <pool type="dir">
    <name>haas_headnodes</name>
    <target>
      <path>/var/lib/libvirt/images</path>
    </target>
  </pool>

The directory specified by path must already exist, and be readable and
writable by the ``libvirt`` user. Then activate the pool, and make the it
activate on boot, with::

  virsh --connect qemu:///system pool-start haas_headnodes
  virsh --connect qemu:///system pool-autostart haas_headnodes

Get a base image from
http://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img,
and put it in the storage pool directory::

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
        <driver name='qemu' type='qcow'/>
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

Many of these fields are probably not needed, but we have not tested this
thoroughly. Further, this set of XML duplicates the path to storage
directory; this seems unnecessary.

Database
------------

HaaS currently supports SQLite for maintaining state. Because SQLAlchemy is
used as a database access layer, other DBs can and should be easily supported
in future releases. The database must be readable and writable by the HaaS
user.  Running the following command as ``haas_user`` will create it (in the
location specified in ``haas.cfg``) and initialize its tables::

  haas init_db

Running the Server under Apache
-------------------------------

HaaS consists of two services: an API server and a networking server. The
former is a WSGI application, which we recommend running with Apache's
``mod_wsgi``. Create a file ``/etc/httpd/conf.d/wsgi.conf``, with the contents::

  LoadModule wsgi_module modules/mod_wsgi.so
  WSGISocketPrefix run/wsgi
  
  <VirtualHost 127.0.0.1:80>
    ServerName 127.0.0.1
    WSGIDaemonProcess haas_user user=haas_user group=haas_user threads=2
    WSGIScriptAlias / /var/www/haas/haas.wsgi
    <Directory /var/www/haas>
      WSGIProcessGroup haas_user
      WSGIApplicationGroup %{GLOBAL}
      Order deny,allow
      Allow from all
    </Directory>
  </VirtualHost>

(The file may already exist, with just the ``LoadModule`` option. If so, it is
safe to replace it.)

If you haven't already, create the directory that will contain the HaaS WSGI module::

 sudo mkdir /var/www/haas/

Copy the file ``haas.wsgi`` from the top of the haas source tree to the
location indicated by the ``WSGIScriptAlias`` option. The virtual host and
server name should be set according to the hostname (and port) by which clients
will access the api. Then, restart Apache::

  sudo service httpd restart

You should also set apache to start on boot::

  sudo chkconfig httpd on

The networking server may be started by running::

  haas serve_networks &

as the HaaS user. To make this happen on boot, add the following to ``/etc/rc.local``::

  (cd /var/lib/haas && su haas_user -c 'haas serve_networks') &

Congratulations- at this point, you should have a functional HaaS service running!

Describe datacenter resources
===================================

For HaaS to do anything useful, you must use the HaaS API to populate the
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

