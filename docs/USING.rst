Using HIL as a Client
======================

Interaction with HIL occurs via its REST API. The high-level semantics of the
API are documented in `API Description <apidesc.html>`_, and the mapping to HTTP is
described in `REST API <rest_api.html>`_.

The ``hil`` command line tool is a wrapper around this API. Running ``hil
help`` will display an overview of the available commands. To tell ``hil``
which HIL instance to use, be sure to do one of:

1. Set the ``HIL_ENDPOINT`` environmental variable. An example (using
   the default port used when running ``hil-admin run-dev-server``) would be
   ``http://127.0.0.1:5000``
2. Ensure that there is a ``hil.cfg`` in the current directory which contains
   a valid ``client`` section. A valid config file in this case could look
   like

::

   [client]
   endpoint = http://127.0.0.1:5000

* If both configuration methods are present, the ``HIL_ENDPOINT`` environmental variable will take precedence over whatever is contained within ``hil.cfg``.
* Though insignificant in some circumstances, the presence or absence of trailing slashes within the endpoint URL can cause issues in communicating with the HIL server, such as "404" errors. For example, using ``http://127.0.0.1:5000`` vs ``http://127.0.0.1:5000/``.

If using the basic auth/database auth backend, you must set the environment
variables ``HIL_USERNAME`` and ``HIL_PASSWORD`` to the correct credentials.

If using the auth/keystone auth backend, first make sure that the keystonemiddleware library is installed by running ``pip install keystonemiddleware``.
Next, ensure that there are OS environment variables set for the following OpenStack authentication credentials: ``OS_AUTH_URL``, ``OS_USERNAME``, ``OS_PASSWORD``, ``OS_PROJECT_NAME``.

Deploying Machines
------------------

The most basic workflow for deploying machines onto a set of nodes allocated
with HIL is as follows. First, create a headnode, and attach it to the network
that the hardware nodes PXE boot off of.  Then, enter the headnode by VNCing to
it from the headnode host. The VNC port can be found with the REST
``show_headnode`` call. Authentication support `is slated
<https://github.com/CCI-MOC/hil/issues/352>`_ for a future release. From
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

Usage examples
---------------

Included here with are some examples about

* Interacting with HIL API directly using the curl utility.

* And using equivalent cli calls are also included.


1) Register a switch with HIL:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Switch name:** mockswitch01
- **Switch type:** mock
- **Host name:**   switchhost01
- **User name:**   switchuser01
- **Password:**    password1234

api call

::

    curl -X put http://127.0.0.1:5000/v0/switch/mockswitch01 -d '
        {"type": "http://schema.massopencloud.org/haas/v0/switches/mock",
        "hostname": "switchhost01",
        "username": "switchuser01",
        "password": "password1234"}'

cli call

::

    $ hil switch register mockswitch02 mock switchhost01 switchuser01 password1234

2) Registering a Node
^^^^^^^^^^^^^^^^^^^^^

- **Node name:**  dummyNoderHIL-02
- **OBMd uri: ``https://obmd.example.com/node/node-02``**
- **OBMd admin token: d7c9e587124fb1cb0d03f79933a9ce28**

For a node with the above information, use the following api call:

::

     curl -X PUT http://127.0.0.1:5001/v0/node/dummyNode01 -d '{
     >     "obmd": {
     >         "uri": "https://obmd.example.com/node/node-02",
     >         "admin_token": "d7c9e587124fb1cb0d03f79933a9ce28"
     >     }
     > }'

Corresponding cli calls will be as follows:

::

     $ hil node register dummyNoderHIL-02 \
             https://obmd.example.com/node/node-02  \
             d7c9e587124fb1cb0d03f79933a9ce28

3) Creating a Project in HIL
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


- **Project name:** mockproject01

api call

::

    curl -X put http://127.0.0.1:5000/v0/project/mockproject01

cli call

::

    $ hil project create mockproject01

4) Register a node in HIL
^^^^^^^^^^^^^^^^^^^^^^^^^^^


- **Node name:** mocknode01
- **Node type:** mock
- **Host name:** mockhost01
- **User name:** nodeuser01
- **Password:** password1234

api call

::

    curl -X put http://127.0.0.1:5000/v0/node/mocknode01 -d '
    > {"type": "http://schema.massopencloud.org/haas/v0/nodes/mock",
    > "hostname": "mockhost01",
    > "username": "nodeuser01",
    > "password": "password1234"}'

cli call

::

    $ hil node register mocknode01 mock mockhost01 nodeuser01 password1234

4) Creating a Network in HIL
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


- **Network name:** mocknetwork01
- **owner:** admin
- **access:** mockproject
- **net_id:** 101

api call

::

    curl -X put http://127.0.0.1:5000/v0/network/mocknetwork01 -d '
        {"owner": "admin",
        "access": "mockproject",
        "net_id": "101"}'

cli call

::

    $ hil network create mocnetwork01 admin mockproject 101
