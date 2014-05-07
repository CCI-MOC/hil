user_create  <user_label> <password>

[POST]   /user  {label:'alice',password:'alice'}
[DELETE] /user/alice


group_add_user    <group_label> <user_label>
group_add_netowrk <group_label> <network_label>

[POST] /group/students/user {label:'alice'}
[POST] /group/students/network {label:'vlan101'}


project_create   <project_label><group_label>
project_delete   <project_label>

[POST] /project {label:'project1',group_label:'student'}
[DELETE] /project/project1


network_create              <network_label> <group_label>
network_delete              <network_label>

[POST] /network {label:'vlan101',group_label:'student'}
[DELETE] /network/vlan101

headnode_create <hn_label> <group_label>
headnode_delete <hn_label>

[POST] /headnode {label:'vm1',group_label:'student'}
[DELETE] /headnode/vm1

project_connect_headnode <hn_label> <project_label>
project_detach_headnode <hn_label> <project_label>
[POST] /project/project1/headnode {label:'vm1'}
[DELETE] /project/project1/headnode/vm1




project_connect_node        <project_label> <node_label> 
project_detach_node         <project_label> <node_label>
[POST] /project/project1/node {label:'node1'}
[DELETE] /project/project1/node/node1


project_connect_network     <project_label> <network_label>
project_detach_network      <project_label> <network_label>
project deploy              <project_label>

[POST]   /project/network {label:'vlan101'}
[DELETE] /project/network/vlan101
[PUT]    /project/project1 {deployed:True}


node_connect_network        <node_label> <nic_label> <network_label>
node_detach_network         <node_label> <nic_label>

[POST]   /network/vlan101/node {label:'node1',nic_label:'ipmi'}
[DELETE] /network/vlan101/node/node1



headnode_create_hnic        <hn_label> <hnic_label> 
headnode_delete_hnic        <hn_label> <hnic_label>
headnode_connect_network    <hn_label> <hnic_label> <network>
headnode_detach_network     <hn_label> <hnic_label>
[POST]   /headnode/vm1/hnic {label:'ipmi'}
[DELETE] /headnode/vm1/hnic/ipmi
[POST]   /headnode/vm1/network {label:'ipmi',network_label:'vlan101'}
[DELETE] /headnode/vm1/network/ipmi




show [ group | project | vm | port | nic | hnic | vlan | switch |
  node | user ] <obj> 
[GET] /group
      /project
      /headnode
      /port
      /hnic
      /nic
      /vlan
      /switch
      /node
      /user
