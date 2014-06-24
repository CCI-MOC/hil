
* `{foo=bar, baz=quux}` denotes http form data (in the body of the request).
* All *_create operations, with the exception of users and groups, have an
  implicit group field to their request payload. i.e.
  `foo_create <foo> <bar> {baz=<bar>}` is a shorthand for
  `foo_create <foo> <bar> <group_label> {baz=<bar>, group=<group_label>)`.

Full Api spec:

    user_create  <user_label> <password>
    user_delete  <user_label>
    [PUT]    /user/<user_label> {password=<password>}
    [DELETE] /user/<user_label>

    group_add_user    <group_label> <user_label>
    group_add_network <group_label> <network_label>
    [POST] /group/<group_label>/add_user {user=<user_label>}
    [POST] /group/<group_label>/add_network {network=<network_label>}

    project_create <project_label>
    project_delete <project_label>
    [PUT]    /project/<project_label>
    [DELETE] /project/<project_label>

    network_create <network_label>
    network_delete <network_label>
    [PUT]    /network/<network_label>
    [DELETE] /network/<network_label>

    headnode_create <hn_label>
    headnode_delete <hn_label>
    [PUT]    /headnode/<hn_label>
    [DELETE] /headnode/<hn_label>

    project_connect_headnode <project_label> <hn_label>
    project_detach_headnode  <project_label> <hn_label>
    [POST] /project/<project_label>/connect_headnode {headnode=<hn_label>}
    [POST] /project/<project_label>/detach_headnode {headnode=<hn_label>}

    project_connect_node <project_label> <node_label>
    project_detach_node  <project_label> <node_label>
    [POST] /project/<project_label>/connect_node {node=<node_label>}
    [POST] /project/<project_label>/detach_node {node=<node_label>}

    project_connect_network <project_label> <network_label>
    project_detach_network  <project_label> <network_label>
    project_deploy          <project_label>
    [POST] /project/<project_label>/connect_network {network=<network_label>}
    [POST] /project/<project_label>/detach_network {network=<network_label>}
    [POST] /project/<project_label>/deploy

    node_connect_network <node_label> <nic_label> <network_label>
    node_detach_network  <node_label> <nic_label>
    [POST] /node/<node_label>/nic/<nic_label>/connect_network {network=<network_label>}
    [POST] /node/<node_label>/nic/<nic_label>/detach_network {network=<network_label>}

    headnode_create_hnic     <hn_label> <hnic_label>
    headnode_delete_hnic     <hn_label> <hnic_label>
    [PUT]    /headnode/<hn_label>/hnic/<hnic_label>
    [DELETE] /headnode/<hn_label>/hnic/<hnic_label>

    headnode_connect_network <hn_label> <hnic_label> <network_label>
    headnode_detach_network  <hn_label> <hnic_label>
    [POST]   /headnode/<hn_label>/hnic/<hnic_label>/connect_network {network=<network_label>}
    [POST]   /headnode/<hn_label>/hnic/<hnic_label>/detach_network {network=<network_label>}
