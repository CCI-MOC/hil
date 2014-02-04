import haas.control

haas.control.create_node(1)
haas.control.create_node(2)
haas.control.create_node(3)


haas.control.create_nic(17,'00:23:ae:92:99:2d','pxe')
haas.control.create_nic(16,'00:0e:0c:85:ce:ca','pxe')
haas.control.create_nic(15,'c8:3a:35:df:02:fd','pxe')
haas.control.create_nic(5,'c8:3a:35:de:ff:03','data0')
haas.control.create_nic(4,'00:23:ae:89:6c:44','data0')
haas.control.create_nic(3,'00:23:ae:92:9e:8a','data0')

haas.control.add_nic(17,1)
haas.control.add_nic(16,2)
haas.control.add_nic(15,3)

haas.control.create_switch(1,'dell')

haas.control.create_port(17,1,17)
haas.control.create_port(16,1,16)
haas.control.create_port(15,1,15)
haas.control.create_port(5,1,5)
haas.control.create_port(4,1,4)
haas.control.create_port(3,1,3)


haas.control.connect_nic(17,17)
haas.control.connect_nic(16,16)
haas.control.connect_nic(16,16)


