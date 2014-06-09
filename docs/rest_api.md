
    user_create  <user_label> <password>
    [PUT]   /user/alice  {password:'alice'}
    [DELETE] /user/alice


    group_add_user    <group_label> <user_label>
    group_add_network <group_label> <network_label>
    [PUT] /students/user/alice
    [PUT] /students/network/vlan101


    project_create   <project_label><group_label>
    project_delete   <project_label>
    [PUT] /students/project/project1
    [DELETE] /students/project/project1


    network_create              <network_label> <group_label>
    network_delete              <network_label>
    [PUT] /students/network/vlan101
    [DELETE] /students/network/vlan101
    
    
    
    headnode_create <hn_label> <group_label>
    headnode_delete <hn_label>
    [PUT] /students/headnode/vm1
    [DELETE] /students/headnode/vm1

    project_connect_headnode <hn_label> <project_label>
    project_detach_headnode <hn_label> <project_label>
    #need a <group_label> ?
    [PUT] /students/project1/headnode/vm1
    [DELETE] /students/project/project1/headnode/vm1


    project_connect_node        <project_label> <node_label> 
    project_detach_node         <project_label> <node_label>
    [PUT] /students/project/project1/node/n1
    [DELETE] /students/project/project1/node/n1


    project_connect_network     <project_label> <network_label>
    project_detach_network      <project_label> <network_label>
    #add a <group_label>?
    [PUT]   /students/project/project1/network/vlan1
    [DELETE] /students/project/project1/network/vlan1
    
    project_deploy              <project_label>
    [POST]    /project/project1/deploy


    node_connect_network        <node_label> <nic_label> <network_label>
    node_detach_network         <node_label> <nic_label>

    [PUT]   /students/network/vlan101/node/n1 {nic_label:'ipmi'}
    [DELETE] /students/network/vlan101/node/n1



    headnode_create_hnic        <hn_label> <hnic_label> 
    headnode_delete_hnic        <hn_label> <hnic_label>
    headnode_connect_network    <hn_label> <hnic_label> <network>
    headnode_detach_network     <hn_label> <hnic_label>
    [PUT]   /headnode/vm1/hnic {label:'ipmi'}
    [DELETE] /headnode/vm1/hnic/ipmi
    [PUT]   /headnode/vm1/network/ipmi {network_label:'vlan101'}
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
