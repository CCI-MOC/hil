
* `{foo=bar, baz=quux}` denotes http form data (in the body of the request).

Full Api spec:

    user_create  <user_id> <password>
    user_delete  <user_id>
    [PUT]    /user/<user_id> {password=<password>}
    [DELETE] /user/<user_id>

    group_add_user    <group_id> <user_id>
    group_add_network <group_id> <network_id>
    [POST] /group/<group_id>/add_user {user=<user_id>}
    [POST] /group/<group_id>/add_network {network=<network_id>}

    project_create <project_id> <group_id>
    project_delete <project_id>
    [PUT]    /project/<project_id> {group=<group_id>}
    [DELETE] /project/<project_id>

    network_create <network_id> <group_id>
    network_delete <network_id>
    [PUT]    /network/<network_id> {group=<group_id>}
    [DELETE] /network/<network_id>

    headnode_create <hn_id> <group_id>
    headnode_delete <hn_id>
    [PUT]    /headnode/<hn_id> {group=<group_id>}
    [DELETE] /headnode/<hn_id>

    project_connect_headnode <project_id> <hn_id>
    project_detach_headnode  <project_id> <hn_id>
    [POST] /project/<project_id>/connect_headnode {headnode=<hn_id>}
    [POST] /project/<project_id>/detach_headnode {headnode=<hn_id>}

    project_connect_node <project_id> <node_id>
    project_detach_node  <project_id> <node_id>
    [POST] /project/<project_id>/connect_node {node=<node_id>}
    [POST] /project/<project_id>/detach_node {node=<node_id>}

    project_connect_network <project_id> <network_id>
    project_detach_network  <project_id> <network_id>
    project_deploy          <project_id>
    [POST] /project/<project_id>/connect_network {network=<network_id>}
    [POST] /project/<project_id>/detach_network {network=<network_id>}
    [POST] /project/<project_id>/deploy

    node_connect_network <node_id> <nic_id> <network_id>
    node_detach_network  <node_id> <nic_id>
    [POST] /node/<node_id>/nic/<nic_id>/connect_network {network=<network_id>}
    [POST] /node/<node_id>/nic/<nic_id>/detach_network {network=<network_id>}

    headnode_create_hnic <headnode_id> <hnic_id>
    headnode_delete_hnic <headnode_id> <hnic_id>
    [PUT]    /headnode/<hn_id>/hnic/<hnic_id>
    [DELETE] /headnode/<hn_id>/hnic/<hnic_id>

    headnode_connect_network <hn_id> <hnic_id> <network_id>
    headnode_detach_network  <hn_id> <hnic_id> <network_id>
    [POST] /headnode/<hn_id>/hnic/<hnic_id>/connect_network {network=<network_id>}
    [POST] /headnode/<hn_id>/hnic/<hnic_id>/detach_network {network=<network_id>}

    node_register <node_id>
    node_delete   <node_id>
    [PUT]    /node/<node_id>
    [DELETE] /node/<node_id>

    node_register_nic <node_id> <nic_id> <mac_addr>
    node_delete_nic   <node_id> <nic_id>
    [PUT]    /node/<node_id>/nic/<nic_id> {mac_addr=<mac_addr>}
    [DELETE] /node/<node_id>/nic/<nic_id>

    switch_register  <switch_id> <driver> <num_ports>
    switch_delete    <switch_id>
    [PUT]    /switch/<switch_id> {driver=<driver>, num_ports=<num_ports>}
    [DELETE] /switch/<switch_id>

    #### TODO FIXME:  Specify the remaining ones
    nic_connect_switch <node_id> <nic_id> <switch_id> <port>
    import_vlan <network_id> <vlan_id>
    block_user <user_id>
    unblock_user <user_id>
