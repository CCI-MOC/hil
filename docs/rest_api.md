
* `{"foo": <bar>, "baz": <quux>}` denotes a JSON object (in the body of 
  the request).

Full Api spec:

    user_create  <user_label> <password>
    user_delete  <user_label>
    [PUT]    /user/<user_label> {password=<password>}
    [DELETE] /user/<user_label>

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

    node_connect_network <node_label> <nic_label> <network_label>
    node_detach_network  <node_label> <nic_label>
    [POST] /node/<node_label>/nic/<nic_label>/connect_network {"network":<network_label>}
    [POST] /node/<node_label>/nic/<nic_label>/detach_network

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
