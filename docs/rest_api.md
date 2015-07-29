This file documents the HaaS REST API in detail.

# How to read

Each possible API call had a entry below containing:

* an HTTP method and URL path, including possible `<parameters>` in the
  path to be treated as arguments.
* Optionally, a summary of the request body (which will always be a JSON
  object).
* A human readable description of the semantics of the call
* A summary of the response body for a successful request. Many calls do
  not return any data, in which case this is omitted.
* A list of possible errors.

In addition to the error codes listed for each API call, HaaS may return
a `400 Bad Request` if something is wrong with the request (e.g.
malformed request body), or `401 Unauthorized` if the user does not have
permission to execute the supplied request.

Below is an example.

## my_api_call

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

Possible errors:

* 418, if `<thing>` is a teapot.
* 409, if:
  * `<thing>` does not exist
  * `<thing>` is busy


* `{"foo": <bar>, "baz": <quux>}` denotes a JSON object (in the body of
  the request).

# Full API Specification

## Users

### user_create

`PUT /user/<username>`

Request body:

    {
        "password": <plaintext-password>
    }

Create a new user whose password is `<plaintext-password>`.

Possible errors:

* 409, if the user already exists

### user_delete

`DELETE /user/<username>`

Delete the user whose username is `<username>`

Possible errors:

* 404, if the user does not exist

## Networks

### network_create

`PUT /network/<network>`

Request Body:

    {
        "creator": <creator>,
        "access": <access>,
        "net_id": <net_id>
    }

Create a network. For the semantics of each of the fields, see
`docs/network.md`.

Possible errors:

* 409, if a network by that name already exists.
* See also bug #461

### network_delete

`DELETE /network/<network>`

Delete a network. The user's project must be the creator of the network,
and the network must not be connected to any nodes or headnodes.
Finally, there may not be any pending actions involving the network.

Possible Errors:

* 404, if the network does not exist
* 409 if:
    * The network is connected to a node or headnode.
    * There are pending actions involving the network.

### show_network

`GET /network/<network>`

View detailed information about `<network>`.

The result must contain the following fields:

* "name", the name of the network
* "channels", description of legal channel identifiers for this network.
  This is a list of channel identifiers, with possible wildcards. The
  format of these is driver specific, see below.
* "creator", the name of the project which created the network, or
  "admin", if it was created by an administrator.

The result may also contain the following fields:

* "access" -- if this is present, it is the name of the project which
  has access to the network. Otherwise, the network is public.

Response body (on success):

    {
        "name": <network>,
        "channels": <chanel-id-list>,
        "creator": <project or "admin">,
        "access": <project with access to the network> (Optional)
    }

Possible errors:

* 404, if the network does not exist.

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

### node_connect_network

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

Possible errors:

* 409, if:
  * The current project does not control `<node>`.
  * The current project does not have access to `<network>`.
  * There is already a pending network operation on `<nic>`.
  * `<network>` is already attached to `<nic>` (possibly on a different channel).
  * The channel identifier is not legal for this network.

### node_detach_network

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

Possible Errors:

* 409, if:
  * The current project does not control `<node>`.
  * There is already a pending network operation on `<nic>`.
  * `<network>` is not attached to `<nic>`.

## Nodes

### node_register

`PUT /node/<node>`

Register a node named `<node>` with the database.

Possible errors:

* 409, if a node with the name `<node>` already exists

### node_delete

`DELETE /node/<node>`

Delete the node named `<node>` from the database.

Possible errors:

* 404 if the node does not exist

### node_register_nic

`PUT /node/<node>/nic/<nic>`

Request Body:

    {
        "mac_addr": <mac_addr>
    }

Register a nic named `<nic>` belonging to `<node>`. `<mac_addr>` should
be the nic's mac address. This isn't used by HaaS itself, but is useful
for users trying to configure their nodes.

Possible errors:

* 404 if `<node>` does not exist
* 409 if `<node>` already has a nic named `<nic>`

### node_delete_nic

`DELETE /node/<node>/nic/<nic>`

Delete the nic named `<nic>` and belonging to `<node>`.

Possible errors:

* 404 if `<nic>` or `<node>` does not exist.

### node_power_cycle

`POST /node/<node>/power_cycle`

Power cycle the node named `<node>`, and set it's next boot device to
PXE.

Possible errors:

* 404, if `<node>` does not exist.

### list_free_nodes

`GET /free_nodes`

Return a list of free/available nodes.

Response body:

    [
        "node-1",
        "node-2",
        ...
    ]

### list_project_nodes

`GET /project/<project>/nodes`

List all nodes belonging to the given project

Response body:

    [
        "node-1",
        "node-2",
        ...
    ]

Possible errors:

* 404 if `<project>` does not exist

## Projects

### project_create

`PUT /project/<project>`

Create a project named `<project>`

Possible Errors:

* 409, if the project already exists

### project_delete

`DELETE /project/<project>`

Delete the project named `<project>`

Possible Errors:

* 409, if:
  * The project does not exist
  * The project still has resources allocated to it:
    * nodes
    * networks
    * headnodes

### list_projects

`GET /projects`

Return a list of all projects in HaaS

Response body:

    [
        "manhattan",
        "runway",
        ...
    ]

# TODO

These api calls still need to be documented in detail, but the below
provides a summary:

    headnode_create <hn_label> <project_label> <base_img>
    headnode_delete <hn_label>
    headnode_start <hn_label>
    headnode_stop <hn_label>
    [PUT]    /headnode/<hn_label> {"project":<project_label>, "base_img":<base_img>}
    [DELETE] /headnode/<hn_label>
    [POST] /headnode/<hn_label>/start
    [POST] /headnode/<hn_label>/stop

    project_connect_node <project_label> <node_label>
    project_detach_node  <project_label> <node_label>
    [POST] /project/<project_label>/connect_node {"node":<node_label>}
    [POST] /project/<project_label>/detach_node {"node":<node_label>}

    headnode_create_hnic <headnode_label> <hnic_label>
    headnode_delete_hnic <headnode_label> <hnic_label>
    [PUT]    /headnode/<hn_label>/hnic/<hnic_label>
    [DELETE] /headnode/<hn_label>/hnic/<hnic_label>

    headnode_connect_network <hn_label> <hnic_label> <network_label>
    headnode_detach_network  <hn_label> <hnic_label>
    [POST] /headnode/<hn_label>/hnic/<hnic_label>/connect_network {"network":<network_label>}
    [POST] /headnode/<hn_label>/hnic/<hnic_label>/detach_network

## Switches

### switch_register

Register a network switch of type `<type>`

`<type>` (a string) is the type of network switch. The possible values
depend on what drivers HaaS is configured to use. The remainder of the
fields are driver-specific; see the documentation for the driver in
question (in `docs/network-drivers.md`.

`PUT /switch/<switch>`

Request body:

    {
        "type": <type>,
        (extra args; depends on <type>)
    }

Possible Errors:

* 409, if a switch named `<switch>` already exists.

### switch_delete

`DELETE /switch/<switch>`

Delete the switch named `<switch>`.

Prior to deleting a switch, all of the switch's ports must first be
deleted.

Possible Errors:

* 404, if the named switch does not exist
* 409, if not all of the switch's ports have been deleted.

### switch_register_port

`PUT /switch/<switch>/port/<port>`

Register a port `<port>` on `<switch>`.

The permissable values of `<port>`, and their meanings, are switch
specific; see the documentation for the apropriate driver for more
information.

Possible Errors:

* 404, if the named switch does not exist
* 409, if the port already exists

### switch_delete_port

`DELETE /switch/<switch>/port/<port>`

Delete the named `<port>` on `<switch>`.

Prior to deleting a port, any nic attached to it must be removed.

Possible Errors:

* 404, if the port or switch does not exist
* 409, if there is a nic attached to the port.

---

    port_connect_nic <port_no> <node_label> <nic_label>
    port_detach_nic  <port_no>
    [POST] /port/<port_no>/connect_nic
    [POST] /port/<port_no>/detach_nic

    import_vlan <network_label> <vlan_label>
    block_user <user_label>
    unblock_user <user_label>

    list_project_headnodes <project> -> [
            "<headnode1_name>",
            "<headnode2_name>",
            ...
        ]
    [GET] /project/<project>/headnodes

    show_node <node> ->
        {
            "name": "box02",
            "free": true,
            "nics": ["ipmi", "pxe", "external",...]
        }
    [GET] /node/<node>

    show_headnode <headnode> ->
        {
            "name": "hn04",
            "project": "projectname",
            "nics": ["ipmi", "pxe", "public", ...]
        }
    [GET] /headnode/<headnode>
