# Overview

This file describes the HIL Api. We first describe the main objects,
then users and security model, and finally provide a full reference for
the API.

## Objects in the HIL

* project - a grouping of resources (e.g., headnodes, nodes, networks).
* node - a physical node.  Either unallocated or belongs to a project.  Has
  one or more NICs attached to it.
* headnode - a controlling machine for a project, today a VM, assigned to one
  project
* NIC - network card, identified by a user-specified label (e.g., PXE, ipmi,
  user1, silly) will have a visible ethernet mac address (or equivalent unique
  number for other network types), and is always part of one node and
  connected to at most one port.
* HNIC - headnode network card, identified by a user-specified label (e.g.,
  PXE, ipmi, user1, silly), and is always part of one headnode.
* port - a port to which NICs can be connected.  Only visible to admins.
* network - a network, today implemented as a VLAN, that NICs and HNICs can be
  connected to.  See networks.md for more details.

The authentication system is pluggable. Authentication mechanisms are
provided by extensions (see `extensions.md`), but the rules about who is
allowed to access what are dictated by HIL core. Operations etiher
require administratie priilieges, or access to a particular project.

Of note, "users" are not a concept that HIL core understands, though
some of the individual auth extensions do.

## API design philosophy

We provide the most basic API that we can, and attempt to impose no structure
that is not required for authorization purposes.

- A 'project' is merely an authorization domain.  It is reasonable to have
  logically independent groupings of resources within one project, but the
  HIL will not help you create such a structure.  Policies like this belong
  in higher-level tools built on top of the hil.

- We considered having a mechanism for staging a large number of networking
  changes and performing them all-together, and even potentially allowing
  roll-back.  Instead, we simply have API calls to connect a NIC to a network,
  and to disconnect it.  All other functionalities can be built on top of
  this.

There is no garbage-collection of objects.  If an object is being used
somehow, it cannot be deleted.  For example, if a node is on a network, the
user can neither de-allocate the node nor delete the network.  They must first
detach the node from the network.  (The one exception to this is that, when
deleting a headnode, all of its HNICs are deleted with it.  This is due to a
technical limitation---we cannot currently dynamically add and remove HNICs.)

Most objects are identified by "labels" that are globally unique, e.g., nodes,
networks, groups, users, headnodes.  While we may eventually change this, it
seems a reasonable limitation for now that simplifies the implementation and
will allow potential sharing of resources. The system will return an error if
a second user tries to create an object with an already existing label. The
one exception is NICs, where the label is unique only on a per-node
basis.

# API Reference

## How to read

Each possible API call has an entry below containing:

* an HTTP method and URL path, including possible `<parameters>` in the
  path to be treated as arguments.
* Optionally, a summary of the request body (which will always be a JSON
  object).
* A human readable description of the semantics of the call
* A summary of the response body for a successful request. Many calls do
  not return any data, in which case this is omitted.
* Any authorization requirements, which could include:
  * Administrative access
  * Access to a particular project or
  * No special access
 In general, administrative access is sufficient to perform any action.
* A list of possible errors.

In addition to the error codes listed for each API call, HIL may
return:

* 400 if something is wrong with the request (e.g. malformed request
  body)
* 401 if the user does not have permission to execute the supplied
  request.
* 404 if the api call references an object that does not exist
  (obviously, this is acceptable for calls that create the resource).

Below is an example.

### my_api_call

`POST /url/path/to/<thing>`

Request Body:

    {
        "some_field": "a value",
        "this-is-an-example": true,
        "some-optional-field": { (Optional)
            "more-fields": 12352356,
            ...
        }
    }

Attempt to do something mysterious to `<thing>` which must be a coffee
pot, and must not be in use by other users. If successful, the response
will include some cryptic information.

Response Body (on success):

    {
        "some-info": "Hello, World!",
        "numbers": [1,2,3]
    }

Authorization requirements:

* No special access.

Possible errors:

* 418, if `<thing>` is a teapot.
* 409, if:
  * `<thing>` does not exist
  * `<thing>` is busy


* `{"foo": <bar>, "baz": <quux>}` denotes a JSON object (in the body of
  the request).

## Core API Specification

API calls provided by the HIL core. These are present in all
installations.

### Networks

#### network_create

`PUT /network/<network>`

Request Body:

    {
        "owner": <owner>,
        "access": <access>,
        "net_id": <net_id>
    }

Create a network. For the semantics of each of the fields, see
[Networks](./networks.html).

Authorization requirements:

* If net_id is `''` and owner and access are the same project, then
  access to that project is required.
* Otherwise, administrative access is required.

Possible errors:

* 409, if a network by that name already exists.
* See also bug #461

#### network_delete

`DELETE /network/<network>`

Delete a network. The user's project must be the owner of the network,
and the network must not be connected to any nodes or headnodes.
Finally, there may not be any pending actions involving the network.

Authorization requirements:

* If the owner is a project, access to that project is required.
* Otherwise, administrative access is required.

Possible Errors:

* 409 if:
    * The network is connected to a node or headnode.
    * There are pending actions involving the network.

#### show_network

`GET /network/<network>`

View detailed information about `<network>`.

The result must contain the following fields:

* "name", the name of the network
* "channels", description of legal channel identifiers for this network.
  This is a list of channel identifiers, with possible wildcards. The
  format of these is driver specific, see below.
* "owner", the name of the project which created the network, or
  "admin", if it was created by an administrator.
* "access", a list of projects that have access to the network or null if the network is public
* "connected-nodes": nodes and list of nics connected to network

Response body (on success):

    {
        "name": <network>,
        "channels": <chanel-id-list>,
        "owner": <project or "admin">,
        "access": <project(s) with access to the network/null>
        "connected-nodes": {"<node>": [<list of nics connected to network]}
    }

Authorization requirements:

* If the network is public, no special access is required.
* Otherwise, access to a project in the "access" list or
administrative access is required.
* Admins and network owners can see all nodes connected to network; other users
only see connected nodes that they have access to.

#### Channel Formats

##### 802.1q VLAN based drivers

Channel identifiers for the VLAN based drivers are one of:

* `vlan/native`, to attach the network as the native (untagged) VLAN
* `vlan/<vlan_id>` where `<vlan_id>` is a VLAN id number. This attaches
   the network in tagged, mode, with the given VLAN id.

Additionally, the `show_networks` api call may return the channel identifier
`vlan/*`, which indicates that any VLAN-based channel id may be used.

Where documentation specifies that the network driver should choose a
default channel, the VLAN drivers choose `vlan/native`.

#### list_networks

`GET /networks`

List all networks.

Returns a JSON dictionary of dictionaries, where the exterior dictionary is indexed by
the network name and the value of each key is another dictionary with keys corresponding
to that network's id and projects

The response must contain the following fields:

* "network", the name of a network
* "network_id", the id of the network
* "projects", a list of projects with access to the network or 'None' if network is public

Example Response:

    {
        "netA": {
            "network_id": "101",
            "projects": ["qproj-01", qproj-02"]
        },
        "netB": {
            "network_id": "102",
            "projects": None
        }
    }

Authorization requirements:

* Administrative access is required

#### list_network_attachments

`GET /network/<network>/attachments`

List all nodes that are attached to network <network>.

If optional argument 'project' is supplied, only attached nodes
belonging to the specified project will be listed.

Returns a JSON dictionary of dictionaries with first level key being the name
of the attached node and second level keys being:

* "nic", the name of the nic on which the node is attached
* "channel", the channel on which the attachment exists
* "project", the name of the project which owns the attached node

Example Response:

    {
        "node1": {
             "nic": "nic1",
             "channel" "vlan/native",
             "project": "projectA"
        },
        "node2": {
             "nic": "nic2",
             "channel": "vlan/235",
             "project": "projectB"
        }
    }

Authorization requirements:

* Admins or the project that is the owner can list all attached nodes.
* Other projects can only list their own nodes.

#### network_grant_project_access

`PUT /network/<network>/access/<project>`

Add <project> to access list for <network>.

Authorization requirements:

* Only admins or the network owner can grant a project access to the
network.

Possible Errors:

* 404 - If the network or project does not exist
* 409 - If the project already has access to the network

#### network_revoke_project_access

`DELETE /network/<network>/access/<project>`

Remove <project> from access list for <network>.

Authorization requirements:

* Only admins, the network owner, or the project itself can revoke a
project's access to the network.

Possible Errors:

* 404 - If the network or project does not exist.
* 409 - If the project is the owner of the network.


#### node_connect_network

`POST /node/<node>/nic/<nic>/connect_network`

Request body:

    {
        "network": <network>,
        "channel": <channel> (Optional)
    }

Connect the network named `<network>` to `<nic>` on `<channel>`.

`<channel>` should be a legal channel identifier specified by the output
of `show_network`, above. If `<channel>` is omitted, the driver will choose
a default, which should be some form of "untagged."

Networks are connected and detached asynchronously. If successful, this
API call returns a status code of 202 Accepted, and queues the network
operation to be preformed. Each nic may have no more than one pending
network operation; an attempt to queue a second action will result in an
error.

Authorization requirements:

* Access to the project to which `<node>` is assigned.
* Either `<network>` must be public, or its `"access"` field must name
  the project to which `<node>` is assigned.

Possible errors:

* 409, if:
  * The current project does not control `<node>`.
  * The current project does not have access to `<network>`.
  * There is already a pending network operation on `<nic>`.
  * `<network>` is already attached to `<nic>` (possibly on a different channel).
  * The channel identifier is not legal for this network.

#### node_detach_network

`POST /node/<node>/nic/<nic>/detach_network`

Request body:

    {
        "network": <network>
    }

Detach `<network>` from `<nic>`.

Networks are connected and detached asynchronously. If successful, this
API call returns a status code of 202 Accepted, and queues the network
operation to be preformed. Each nic may have no more than one pending
network operation; an attempt to queue a second action will result in an
error.

If a maintenance pool is configured, the maintenance service will be
notified and the node will be moved into the maintenance project.
Otherwise, the node will go directly to the free pool.
Read `docs/maintenance-pool.md` for more information.

Authorization requirements:

* Access to the project to which `<node>` is assigned.

Possible Errors:

* 409, if:
  * The current project does not control `<node>`.
  * There is already a pending network operation on `<nic>`.
  * `<network>` is not attached to `<nic>`.

### Nodes

#### node_register

Register a node with OBM of <type> and optional metadata

<type> (a string) is the type of OBM. The possible value depends on what drivers
HIL is configured to use. The remainder of the field are driver-specific;
see the documentation of the OBM driver in question (read `docs/obm-drivers.md`).

`PUT /node/<node>`

Request Body:

    {
        "obm": {
            "type": <obm-subtype>, <additional sub-type specific values>
        },
        "metadata": { (Optional)
            "label_1": "value_1",
            "label_2": "value_2"
        }
    }

example provided in USING.rst

Register a node named `<node>` with the database.

Authorization requirements:

* Administrative access.

Possible errors:

* 409, if a node with the name `<node>` already exists

#### node_delete

`DELETE /node/<node>`

Delete the node named `<node>` from the database.

Authorization requirements:

* Administrative access.

#### node_register_nic

`PUT /node/<node>/nic/<nic>`

Request Body:

    {
        "macaddr": <mac_addr>
    }

Register a nic named `<nic>` belonging to `<node>`. `<mac_addr>` should
be the nic's mac address. This isn't used by HIL itself, but is useful
for users trying to configure their nodes.

Authorization requirements:

* Administrative access.

Possible errors:

* 409 if `<node>` already has a nic named `<nic>`

#### node_delete_nic

`DELETE /node/<node>/nic/<nic>`

Delete the nic named `<nic>` and belonging to `<node>`.

Authorization requirements:

* Administrative access.

#### node_power_cycle

`POST /node/<node>/power_cycle`

Request Body:

    {
        "force": <boolean> (Optional, defaults to False)
    }

Power cycle the node named `<node>`, and set it's next boot device to
PXE. If the node is powered off, this turns it on.

Accepts one optional boolean argument that determines whether to soft (default)
or hard reboot the system.

Authorization requirements:

* Access to the project to which `<node>` is assigned (if any) or administrative access.

#### node_set_bootdev

`PUT /node/<node>/boot_device`

Request body:

    {
        "bootdev": <boot device>
    }

The request body consists of JSON with a `bootdev` argument:

Sets the node's next boot device persistently

Authorization requirements:

* Access to the project to which `<node>` is assigned (if any) or administrative access.

##### For IPMI devices

The valid/allowed boot devices are:

* pxe : do a pxe boot (network boot)
* disk: boot from local hard disk
* none: to reset boot order to default.

#### node_power_off

`POST /node/<node>/power_off`

Power off the node named `<node>`. If the node is already powered off,
this will have no effect.

Authorization requirements:

* Access to the project to which `<node>` is assigned (if any) or administrative access.

#### list_nodes

`GET /nodes/<is_free>`

Return a list of all nodes or free/available nodes. The value of `is_free`
can be `all` to return all nodes or `free` to return free/available nodes.

Response body:

    [
        "node-1",
        "node-2",
        ...
    ]

Authorization requirements:

* No special access

#### list_project_nodes

`GET /project/<project>/nodes`

List all nodes belonging to the given project

Response body:

    [
        "node-1",
        "node-2",
        ...
    ]

Authorization requirements:

* Access to `<project>` or administrative access

#### list_project_networks

`GET /project/<project>/networks`

List all networks belonging to the given project

Response body:

    [
        "network-1",
        "network-2",
        ...
    ]

Authorization requirements:

* Access to `<project>` or administrative access

#### show_node

`GET /node/<node>`

Show details of a node.

Returns a JSON object representing a node.
The object will have at least the following fields:

* "name", the name/label of the node (string).
* "project", the name of the project a node belongs to or null if the node does not belong to a project
* "nics", a list of nics, each represented by a JSON object having
  at least the following fields:

    - "label", the nic's label.
    - "macaddr", the nic's mac address.
    - "networks", a JSON object describing what networks are attached to the nic. The keys are channels and the values are the names of networks attached to those channels.
    - "port", the port to which the nic is connected to or
      null if the nic
      is not connected to any port. This field is only visibile if the
      caller is an admin.
    - "switch", the switch that has the port to which the nic is connected
      to or null if the nic is not connected to any port. Just like port,
      this is only visible if the caller is an admin.
* "metadata", a dictionary of metadata objects

Response body when run by a non-admin user:

    {
        "metadata": {
            "EK": "pk"
        },
        "name": "node1",
        "nics": [
            {
                "label": "nic1",
                "macaddr": "01:23:45:67:89",
                "networks": {
                    "vlan/235": "storage",
                    "vlan/native": "pxe"
                }
            },
            {
                "label": "nic2",
                "macaddr": "12:34:56:78:90",
                "networks": {}
            }
        ],
        "project": "project1"
    }


Response body when run by an admin:

    {
        "metadata": {
            "EK": "pk"
        },
        "name": "node1",
        "nics": [
            {
                "label": "nic1",
                "macaddr": "01:23:45:67:89",
                "networks": {
                    "vlan/235": "storage",
                    "vlan/native": "pxe"
                },
                "port": "gi1/0/1",
                "switch": "dell-01"
            },
            {
                "label": "nic2",
                "macaddr": "12:34:56:78:90",
                "networks": {},
                "port": null,
                "switch": null
            }
        ],
        "project": "project1"
    }

Authorization requirements:

* If the node is free, no special access is required.
* Otherwise, access to the project to which `<node>` is assigned is
  required.
* Admin acces to view port and switch information.

### Projects

#### project_create

`PUT /project/<project>`

Create a project named `<project>`

Authorization requirements:

* Administrative access.

Possible Errors:

* 409, if the project already exists

#### project_delete

`DELETE /project/<project>`

Delete the project named `<project>`

Authorization requirements:

* Administrative access.

Possible Errors:

* 409, if:
  * The project does not exist
  * The project still has resources allocated to it:
    * nodes
    * networks
    * headnodes

#### project_connect_node

`POST /project/<project>/connect_node`

Request body:

    {
        "node": <node>
    }

Reserve the node named `<node>` for use by `<project>`. The node must be
free.

Authorization requirements:

* Access to `<project>` or administrative access.

Possible errors:

* 404, if the node or project does not exist.
* 409, if the node is not free.

#### project_detach_node

`POST /project/<project>/detach_node`

    {
        "node": <node>
    }

Return `<node>` to the free pool. `<node>` must belong to the project
`<project>`. It must not be attached to any networks, or have any
pending network actions.

Authorization requirements:

* Access to `<project>` or administrative access.

* 409, if the node is attached to any networks, or has pending network
  actions.

#### list_projects

`GET /projects`

Return a list of all projects in HIL

Response body:

    [
        "manhattan",
        "runway",
        ...
    ]

Authorization requirements:

* Administrative access.

#### node_set_metadata

`PUT /node/<node>/metadata/<label>`

Request Body:

    {
        "value": <value>
    }

Set metadata with `<label>` and `<value>` on `<node>`.

Authorization requirements:

* Administrative access.

#### node_delete_metadata

`DELETE /node/<node>/metadata/<label>`

Delete metadata with `<label>` on `<node>`.

Authorization requirements:

* Administrative access.

### Headnodes

#### headnode_create

`PUT /headnode/<headnode>`

Request body:

    {
        "project": <project>,
        "base_img": <base_img>
    }

Create a headnode owned by project `<project>`, cloned from base image
`<base_img>`. `<base_img>` must be one of the installed base images.

Authorization requirements:

* Access to `<project>` or administrative access

Possible errors:

* 409, if a headnode named `<headnode>` already exists

#### headnode_delete

`DELETE /headnode/<headnode>`

Delete the headnode named `<headnode>`.

Authorization requirements:

* Access to the project which owns `<headnode>` or administrative access.

#### headnode_start

`POST /headnode/<headnode>/start`

Start (power on) the headnode. Note that once a headnode has been
started, it cannot be modified (adding/removing hnics, changing
networks), only deleted --- even if it is stopped.

Authorization requirements:

* Access to the project which owns `<headnode>` or administrative access.

#### headnode_stop

`POST /headnode/<headnode>/stop`

Stop (power off) the headnode. This does a force power off; the VM is
not given the opportunity to shut down cleanly.

Authorization requirements:

* Access to the project which owns `<headnode>` or administrative access.

#### headnode_create_hnic

`PUT /headnode/<headnode>/hnic/<hnic>`

Create an hnic named `<hnic>` belonging to `<headnode>`. The headnode
must not have previously been started.

Authorization requirements:

* Access to the project which owns `<headnode>` or administrative access.

Possible errors:

* 409, if:
  * The headnode already has an hnic by the given name.
  * The headnode has already been started.

#### headnode_delete_hnic

`DELETE /headnode/<headnode>/hnic/<hnic>`

Delete the hnic named `<hnic>` and belonging to `<headnode>`. The
headnode must not have previously been started.

Authorization requirements:

* Access to the project which owns `<headnode>` or administrative access.

Possible errors:

* 409, if the headnode has already been started.

#### headnode_connect_network

`POST /headnode/<headnode>/hnic/<hnic>/connect_network`

Request body:

    {
        "network": <network>
    }

Connect the network named `<network>` to `<hnic>`.

`<network>` must be the name of a network which:

1. the headnode's project has the right to attach to, and
2. was not assigned a specific network id by an administrator (i.e. the
   network id was allocated dynamically by HIL). This constraint is due
   to an implementation limitation, but will likely be lifted in the
   future; see issue #333.

Additionally, the headnode must not have previously been started.

Note that, unlike nodes, headnodes may only be attached via the
native/default channel (which is implicit, and may not be specified).

Rationale: separating headnodes from hil core is planned, and it has
been deemed not worth the development effort to adjust this prior to the
separation. Additionally, headnodes may have an arbitrary number of
nics, and so being able to attach two networks to the same nic is not as
important.

Authorization requirements:

* Access to the project which owns `<headnode>` or administrative access.
* Either `<network>` must be public, or its `"access"` field must name
  the project which owns `<headnode>`.

Possible errors:

* 409, if the headnode has already been started.

#### headnode_detach_network

`POST /headnode/<headnode>/hnic/<hnic>/detach_network`

Detach the network attached to `<hnic>`.  The headnode must not have
previously been started.

Authorization requirements:

* Access to the project which owns `<headnode>` or administrative access.

Possible errors:

* 409, if the headnode has already been started.

#### list_project_headnodes

`GET /project/<project>/headnodes`

Get a list of names of headnodes belonging to `<project>`.

Response body:

    [
        "<headnode1_name>",
        "<headnode2_name>",
        ...
    ]

Authorization requirements:

* Access to `<project>` or administrative access.

#### show_headnode

`GET /headnode/<headnode>`

Get information about a headnode. Includes the following fields:

* "name", the name/label of the headnode (string).
* "project", the project to which the headnode belongs.
* "hnics", a JSON array of hnic names that are attached to this
    headnode.
* "vncport", the vnc port that the headnode VM is listening on; this
    value can be `null` if the VM is powered off or has not been
    created yet.
* "uuid", UUID for the headnode.
* "base_img", the os image that the headnode is running.

Response body:

    {
        "name": <headnode>,
        "project": <projectname>,
        "nics": [<nic1>, <nic2>, ...],
        "vncport": <port number>,
        "uuid": <headnode uuid>,
        "base_img": <headnode base_img>
    }

Authorization requirements:

* Access to the project which owns `<headnode>` or administrative access.

### Switches


### show_switch

`GET /switch/<switch>`

View detailed information about `<switch>`.

The result must contain the following fields:

* "name", the name of the switch
* "ports", a list of the name of the ports which exist on the switch

Response body (on success):

    {
        "name": <switch>,
        "ports": <ports-list>
    }

Authorization requirements:

* Administrative access.

#### switch_register
Register a network switch of type `<type>`

`<type>` (a string) is the type of network switch. The possible values
depend on what drivers HIL is configured to use. The remainder of the
fields are driver-specific; see the documentation for the driver in
question (in `docs/network-drivers.md`.

`PUT /switch/<switch>`

Request body:

    {
        "type": <type>,
        (extra args; depends on <type>)
    }

Authorization requirements:

* Administrative access.

Possible Errors:

* 409, if a switch named `<switch>` already exists.

#### switch_delete

`DELETE /switch/<switch>`

Delete the switch named `<switch>`.

Prior to deleting a switch, all of the switch's ports must first be
deleted.

Authorization requirements:

* Administrative access.

Possible Errors:

* 409, if not all of the switch's ports have been deleted.

#### list_switches

`GET /switches`

Return a list of all switches registered in HIL

Response body:

    [
        "switch1",
        "hickory",
        ...
    ]

Authorization requirements:

* Administrative access.

#### switch_register_port

`PUT /switch/<switch>/port/<port>`

Register a port `<port>` on `<switch>`.

The permissible values of `<port>`, and their meanings, are switch
specific; see the documentation for the appropriate driver for more
information.

Authorization requirements:

* Administrative access.

Possible Errors:

* 409, if the port already exists

#### switch_delete_port

`DELETE /switch/<switch>/port/<port>`

Delete the named `<port>` on `<switch>`.

Prior to deleting a port, any nic attached to it must be removed.

Authorization requirements:

* Administrative access.

Possible Errors:

* 409, if there is a nic attached to the port.

#### port_connect_nic

`POST /switch/<switch>/port/<port>/connect_nic`

Request body:

    {
        "node": <node>,
        "nic": <nic>
    }

Connect a port a node's nic.

Authorization requirements:

* Administrative access.

Possible errors:

* 404, if no port is connected to the given nic.
* 409, if the nic or port is already attached to something.

#### port_detach_nic

`POST /switch/<switch>/port/<port>/detach_nic`

Detach the nic attached to `<port>`.

Authorization requirements:

* Administrative access.

Possible errors:

* 404, if the port is not attached to a nic
* 409, if the port is attached to a node which is not free.

#### port_revert

`POST /switch/<switch>/port/<port>/revert`

Detach the port from all networks.

Authorization requirements:

* Administrative access.

Possible errors:

* 404, if there is no nic attached to `port`
* 409, if there is already a networking action pending on `port`

#### show_port

`GET /switch/<switch>/port/<port>`

Show the node and nic to which the port is connected.

Response body:

    {
        "node": "mynode",
        "nic": "mynic",
        "networks": {"vlan/1511": "mynetwork"}
    }

If there is no nic attached to a port, the response body is just an empty
json object:

    {}

Authorization requirements:

* Administrative access.

Possible errors:

* 404, if the switch and/or port do not exist.

#### list_active_extensions

`GET /active_extensions`

Response Body:

[
    "hil.ext.switches.mock",
    "hil.ext.network_allocators.null",
    ...
]

List all active extensions.

Authorization requirements:

* Administrative access.

## API Extensions

API calls provided by specific extensions. They may not exist in all
configurations.

### The `hil.ext.auth.database` auth backend

#### user_create

`PUT /auth/basic/user/<username>`

Request body:

    {
        "password": <plaintext-password>
        "is-admin": <boolean> (Optional, defaults to False)
    }

Create a new user whose password is `<plaintext-password>`.

Authorization requirements:

* Administrative access.

Possible errors:

* 409, if the user already exists

#### user_delete

`DELETE /auth/basic/user/<username>`

Delete the user whose username is `<username>`

Authorization requirements:

* Administrative access.

#### user_set_admin

'PATCH /auth/basic/user/<user>'

Request Body:

{
    'is_admin': <boolean>
}

Set admin status of user '<user>' to true (admin user) or false (regular user)

Authorization requirements:

* Administrative access.

Possible errors:

* 404, if the user does not exist.

* 409, if the user tries to set own admin privilege

#### user_add_project

`POST /auth/basic/user/<user>/add_project`

Request Body:

{
    "project": <project_name>
}

Add a user to a project.

Authorization requirements:

* Administrative access.

#### user_remove_project

`POST /auth/basic/user/<user>/remove_project`

Request Body:

{
    "project": <project_name>
}

Remove a user from a project.

Authorization requirements:

* Administrative access.
