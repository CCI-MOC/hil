current interface, grew organically:

    group create <group_name>
    node create <node_id>
    node add <node_id> <group_name>
    nic create <nic_id> <mac_addr> <name>
    nic connect <nic_id> <port_id>
    nic add <nic_id> <node_id>
    switch create <switch_id> <script>
    port create <port_id> <switch_id> <port_no>
    vlan create <vlan_id>
    vlan connect <vlan_id> <group_name> <nic_name>
    headnode create
    headnode attach <vm_name> <group_name>
    group deploy <group_name>
    user create <user name> <password>
    show all
    show [ group | vm | port | nic | vlan | switch | node | user ]
    help
    exit

Not clear what was atomic, synchronization model, and there were a
series of inconsistencies.  

There are two classes of users:

1. Administrators: Responsible for configuring the hardware,
   and configuring the HaaS service.
2. Users: Configuring specific groups, allocating nodes to groups,
   deleting groups...

Administrators can shoot themselves (or each other) in the foot.  If
two administrators modify the HaaS service (e.g., add switches, add
nodes, move ports around...) behavior may be non deterministic.
Administrators can block all "Users" from accessing the HaaS service
while they are making changes. 

To users re-configuring a group can shoot each other in the foot, and
are responsible for coordinating among themselves.  They cannot,
however, impact users controlling different groups. 

A user making a series of changes to a group can make all the
individual changes, and only once they are complete "deploy" them to
the switch.  

An administrator can perform "User" activities on any group. 

Objects on the (new model) are:

* node - a physical node
* master_node   - a controlling machine for a group, today a VM
* NIC        	- network cards, identified by a user-specified label (e.g.,
        	  PXE, ipmi, user1, silly) will have a visible
        	  ethernet mac address (or equivalent unique number
        	  for other network types), and is always part of one node
* switch        - a physical network switch, note not visible to
        	  users, just admins
* port        	- a port on a switch, note, not visible to users, just
        	  to admins 
* network        - a network, today implemented as a VLAN

user operations:

    user_create                	<user name> <password>
    user_destroy                <user name>
 
    group_create                <group_label>
    group_destroy               <group_label>
 
    network_create              <network_label>
    network_destroy             <network_label>
 
    headnode_create             <hn_label>
    headnode_destroy            <hn_label>
    group_connect_headnode      <hn_label> <group_label>
    group_detach_headnode       <hn_label> <group_label>
 
    group_connect_node          <node_id> <group_label>
    group_detach_node           <node_id> <group_label>
 
    # networking operations on a group
    group_connect_network       <network_label> 
    group_detach_network        <network_label>
    group deploy                <group_label>
 
    # networking operations on a physical node
    node_connect_network        <node_id> <nic_label> <network_label>
    node_detach_network         <node_id> <nic_label> 
 
    # networking operations on a headnode
    headnode_create_nic         <hn_label> <nic_label> 
    headnode_destroy_nic        <hn_label> <nic_label>
    headnode_connect_network    <hn_label> <nic_label> <network>
    headnode_detach_network     <hn_label> <nic_label> 
 
    # need to work on query interface, you should see only objects in
      your group...
    show all
    show [ group | vm | port | nic | vlan | switch | node | user ]
    help
    exit

admin operations:
    node_create                	<node_id>
    node_destroy                <node_id>
 
    node_create_nic             <node_id> <nic_label> <mac_addr>
    node_destroy_nic            <node_id> <nic_label> 
 
    switch_create               <switch_label> <script> <number_ports>
    switch_destroy              <switch_label> 
 
    nic_connect_switch          <node_id> <nic_label> <switch_label> <port_id>
 
    block_users
    unblock_users


Changes:

* commands start with the name of the containing object
  e.g., node add -> group connect node 
* consistent naming, i.e., connect/disconnect rather than
  attach/add/...
* vlan -> network
* hide internal numbers, e.g. vlan_id, ... instead use lables
* got rid of operations on group of objects, i.e., vlan connect
  operated on all nics with label, which would have forced us to do
  bizzar work if a new nic got added with same label
* connect all words in command with "_" since could be function name
* headnode create specifies a vm_label
* call string names everywhere
* got rid port_id and port_no, always identify port as a switch and
  port number relative to that switch, like nics on a 

Notes:

* does a destroy operation leads to orphaned objects, or does it clean
  up?  I think the latter is necessary, e.g., if you destroy a group,
  and it doesn't destroy all the sub-objects, you might have a network
  still connected to some ports, and the next guy comes along, and
  suddenly we have a security hole... 
* changes to network configuration happen when a 
* network has to be connected to a group before it can be connected 
  to a node in the group, i.e, an group A can give group B access to
  network, group B users can then connect network to nodes in their group
* should it be `node_connect_network` or `network_connect_node`?

* permission model: I didn't put this in, but one possibility...
 * all objects created by user are as part of a group
 * when object is removed from last group, it is deleted
 * an object can be connected to other groups

* how do we associate arbitrary data with an object, e.g., mac
  address... we should have operations to get info about an arbitrary
  object 

* don't really like the use of "group", since I think it should be a
  group of users... would prefer something like a VDC (virtual data
  center), or pool to express a grouping of resources, or perhaps a
  user group and a resource group
