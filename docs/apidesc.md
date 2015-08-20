#HaaS API

First describe the main objects, the users and security model, then
then the actual API.

## Objects in the HaaS

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

Additionally, we provide one built-in authorization model, that adds another kind of object:

* user - a user, with password and login.  Users can have access to any number
  of projects.

## API design philosophy

We provide the most basic API that we can, and attempt to impose no structure
that is not required for authorization purposes.

- A 'project' is merely an authorization domain.  It is reasonable to have
  logically independent groupings of resources within one project, but the
  HaaS will not help you create such a structure.  Policies like this belong
  in higher-level tools built on top of the haas.

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
one exception is NICs, where the label is unique only on a per-node basis.


## User operations:

    # Basic node allocation and network isolation

    network_create              <network_label> <proj_creator> <proj_access> <id>
    network_delete              <network_label>

    project_connect_node        <project_label> <node_label>
    project_detach_node         <project_label> <node_label>

    node_connect_network        <node_label> <nic_label> <network_label>
    node_detach_network         <node_label> <nic_label>

    # Headnode operations

    headnode_create             <hn_label> <project_label>
    headnode_delete             <hn_label>

    headnode_start              <hn_label>
    headnode_stop               <hn_label>

    headnode_create_hnic        <hn_label> <hnic_label>
    headnode_delete_hnic        <hn_label> <hnic_label>

    headnode_connect_network    <hn_label> <hnic_label> <network>
    headnode_detach_network     <hn_label> <hnic_label>

    # IPMI-based operations on nodes

    node_power_cycle           <node_label>

    start_console              <node_label>
    show_console               <node_label>
    stop_console               <node_label>

    # Query interface

    list_free_nodes
    list_project_nodes         <project>
    list_project_networks      <project>
    list_project_headnodes     <project>
    show_node                  <node>
    show_headnode              <headnode>
    show_network               <network>


## Authorization-related operations:

    # Always useful

    project_create              <project_label>
    project_delete              <project_label>

    # Only meaningful with the built-in auth backend

    user_create                 <user_label> <password>
    user_delete                 <user_label>

    project_add_user            <project_label> <user_label>
    project_remove_user         <project_label> <user_label>

# Administrative operations to describe physical configuration

    list_projects

    node_register      <node_label>
    node_delete        <node_label>
    node_register_nic  <node_label> <nic_label> <mac_addr>
    node_delete_nic    <node_label> <nic_label>

    port_register      <port_no>
    port_delete        <port_no>
    port_connect_nic   <port_no> <node_label> <nic_label>
    port_detach_nic    <port_no>
