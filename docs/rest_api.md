
* `{"foo": <bar>, "baz": <quux>}` denotes a JSON object (in the body of 
  the request).

# Full Api spec:

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

### show_network

`GET /network/<network>`

View detailed information about `<network>`.

The result contains the following information:

* The name of the network
* A description of legal channel identifiers for this network. This is a list
  of channel identifiers, with possible wildcards. The format of these is
  driver specific, see below.

Response body (on success):

    {
        "name": <network>
        "channels": <chanel-id-list>
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

Possible Errors:

* 409, if:
  * The current project does not control `<node>`.
  * There is already a pending network operation on `<nic>`.
  * `<network>` is not attached to `<nic>`.

# TODO

These api calls still need to be documented in detail, but the below 
provides a summary:

    project_create <project_label>
    project_delete <project_label>
    [PUT]    /project/<project_label>
    [DELETE] /project/<project_label>

    network_create <network_label> <proj_creator> <proj_access> <net_id>
    network_delete <network_label>
    [PUT]    /network/<network_label> {"creator":<proj_creator>,
                                       "access":<proj_access>,
                                       "net_id":<net_id>}
    [DELETE] /network/<network_label>

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

    node_power_cycle <node_label>
    [POST] /node/<node_label>/power_cycle

    headnode_create_hnic <headnode_label> <hnic_label>
    headnode_delete_hnic <headnode_label> <hnic_label>
    [PUT]    /headnode/<hn_label>/hnic/<hnic_label>
    [DELETE] /headnode/<hn_label>/hnic/<hnic_label>

    headnode_connect_network <hn_label> <hnic_label> <network_label>
    headnode_detach_network  <hn_label> <hnic_label>
    [POST] /headnode/<hn_label>/hnic/<hnic_label>/connect_network {"network":<network_label>}
    [POST] /headnode/<hn_label>/hnic/<hnic_label>/detach_network

    node_register <node_label>
    node_delete   <node_label>
    [PUT]    /node/<node_label>
    [DELETE] /node/<node_label>

    node_register_nic <node_label> <nic_label> <mac_addr>
    node_delete_nic   <node_label> <nic_label>
    [PUT]    /node/<node_label>/nic/<nic_label> {"mac_addr":<mac_addr>}
    [DELETE] /node/<node_label>/nic/<nic_label>

## Switches

### switch_register

Register a network switch of type `<type>`
 
`<type>` (a string) is the type of network switch. The possible values 
depend on what drivers HaaS is configured to use. The remainder of the 
fields are driver-specific; see the documentation for the driver in 
question.

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

Delete the switch named `<switch>.

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

    port_register  <port_no>
    port_delete    <port_no>
    [PUT]    /port/<port_no>
    [DELETE] /port/<port_no>

    port_connect_nic <port_no> <node_label> <nic_label>
    port_detach_nic  <port_no>
    [POST] /port/<port_no>/connect_nic
    [POST] /port/<port_no>/detach_nic

    import_vlan <network_label> <vlan_label>
    block_user <user_label>
    unblock_user <user_label>

    list_free_nodes -> ["<node1_name>", "<node2_name>", ...]
    [GET] /free_nodes

    list_projects -> ["project-runway", "manhattan-project"]
    [GET] /projects

    list_project_nodes <project> -> ["<node1_name>", "<node2_name>", ...]
    [GET] /project/<project>/nodes

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
