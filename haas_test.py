import haas.control

haas.control.create_node(2)
haas.control.create_node(3)
haas.control.create_node(4)


haas.control.create_nic(2,'mac2','pxe')
haas.control.create_nic(3,'mac3','pxe')
haas.control.create_nic(4,'mac4','pxe')

haas.control.add_nic(2,2)
haas.control.add_nic(3,3)
haas.control.add_nic(4,4)

haas.control.create_switch(1,'dell')

haas.control.create_port(2,1,2)
haas.control.create_port(3,1,3)
haas.control.create_port(4,1,4)

haas.control.connect_nic(2,2)
haas.control.connect_nic(3,3)
haas.control.connect_nic(4,4)


