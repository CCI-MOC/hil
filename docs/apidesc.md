#HaaS API

Eventually this will be the final documentation for the API, for now,
it has additional information to give context for the conversation.
We first discuss the original API, then the proposed API.

##Original API
Current interface, grew organically:

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
series of inconsistencies, and we don't have model of permissions...

##Proposed API

First describe the users and security model, then the main objects,
then the actual API.

###Objects on the (new model) are:

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


### Permissions users and synchronization

Users will belong to different groups.  Groups will in turn own
projects.  One special group is
the "admin" group.  

The HaaS does not provide rich synchronization, garbage collection of
orphaned objects (e.g. deleting a node does not delete NICs), ... it
is assumed that its users are sophisticated, and tools are built above
the HaaS service to keep users from shooting themselves in the foot.

However, it does have a number of important requirements: 1) it must
allow administrators to be able to change the system without messing
up users trying to access the system concurrently, 2) it must keep
users from being able to mess up users in other projects..., 3) it
must allow users to be able to configure their systems in a fashion
where their users see a complete set of changes, rather than
intermediate results. 

For the former, admins can block any user not belonging to the admin
group from the system.

For the latter, we will support a "deploy" operation, where users can
make many indivual changes, and then "deploy" them in one operation. 

Administrators can shoot themselves (or each other) in the foot.  If
two administrators modify the HaaS service (e.g., add switches, add
nodes, move ports around...) behavior may be non deterministic.

An administrator can perform "User" activities on any group. 

###User operations:

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

###Admin operations:
    node_create                	<node_id>
    node_destroy                <node_id>
 
    node_create_nic             <node_id> <nic_label> <mac_addr>
    node_destroy_nic            <node_id> <nic_label> 
 
    switch_create               <switch_label> <script> <number_ports>
    switch_destroy              <switch_label> 
 
    nic_connect_switch          <node_id> <nic_label> <switch_label> <port_id>
 
    block_users
    unblock_users


###Changes:

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

###Notes:

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
