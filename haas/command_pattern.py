import re

create_user = re.compile('^create user (\w+) (\w+)$')




# Remove a machine from a group
remove = re.compile('^remove (\S+) from (\w+)$')


# Destroy a vlan
destroy_vlan = re.compile('^destroy vlan (\d+)')

# Show a specific group
show_group = re.compile('^show group (\w+)')
# Show the free elements of a table
show_free_table = re.compile('^show free (\w+)')
# Show a specific table
show_table = re.compile('^show (\w+)')


# Change a group's vlan
change_vlan = re.compile('^change (\w+) vlan to (\d+)')
# Change a group's vm
change_head = re.compile('^change (\w+) head to (\S+)')

#create a node
create_node = re.compile('^node create (\d+)$')
#create a nic
create_nic = re.compile('^nic create (\d+) (\w+) (\w+)$')
#add a nic to node
add_nic = re.compile('^nic add (\d+) (\d+)$')

#connect a nic to port, nic_id, port_id
connect_nic = re.compile('^nic connect (\d+) (\d+)$')

#create a switch
create_switch = re.compile('^switch create (\d+) (\w+)$')
#create a port , port_id, switch_id, port_no
create_port = re.compile('^port create (\d+) (\d+) (\d+)$')

#connect nic to port
connect_nic = re.compile('^nic connect (\d+) (\d+)$')

#create a group_name
create_group = re.compile('^group create (\w+)$')

#deploy a group
deploy_group = re.compile('^group deploy (\w+)$')

#destroy a group
destroy_group = re.compile('^group destroy (\w+)$')
#create a vlan
create_vlan = re.compile('^vlan create (\d+)$')
#connect vlan to a group with nic name
connect_vlan = re.compile('^vlan connect (\d+) (\w+) (\w+)$')

#add a node to group
add_node = re.compile('^node add (\d+) (\w+)$')

#create a headnode
create_headnode = re.compile('^headnode create$')
#attach a headnode to a group
attach_headnode = re.compile('^headnode attach ([\w-]+) (\w+)$');

