Using HaaS as a Client
======================

Interaction with HaaS occurs via its REST API. The high-level semantics of the
API are documented in `apidesc.md <apidesc.md>`_, and the mapping to HTTP is
described in `rest_api.md <rest_api.md>`_.

The ``haas`` command line tool is a wrapper around this API. Running ``haas
help`` will display an overview of the available commands. Just as with ``haas
serve_networks``, ``haas.cfg`` must be in your working directory. But here,
only the ``client`` section is needed, so users without access to the global
configuration file may use a more minimal one.

Deploying Machines
------------------

The most basic workflow for deploying machines onto a set of nodes allocated
with HaaS is as follows. First, create a headnode, and attach it to the network
that the hardware nodes PXE boot off of.  Then, enter the headnode by VNCing to
it from the headnode host. The VNC port can be found with the REST
``show_headnode`` call. Authentication support `is slated
<https://github.com/CCI-MOC/haas/issues/352>`_ for a future release. From
there, you can set up SSH access to the headnode, or you can continue to use
VNC if you prefer.

Next, configure DHCP and TFTP servers that will boot nodes into some automated
install image.  We have an example of this in ``examples/puppet_headnode``.  In
this example, we use Kickstart to automate a Centos install.  Our kickstart
file configures very little of the system, but complicated configuration can be
done this way, especially by using Kickstart to install a tool such as Puppet.

Our setup has one additional trick.  We run a server that, firstly, serves the
Kickstart file, but secondly makes it so each node only PXE boots the installer
once.  The last thing each node does while installing is to tell the server to
delete its symlink from the TFTP config, which will make the machine fall back
to hard-disk booting the installed system.

This is, as the filepath states, merely an example of how you might deploy to
physical nodes.  Existing deployment systems such as Canonical's MAAS have also
been run succesfully.
