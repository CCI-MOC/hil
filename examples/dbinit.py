#!/usr/bin/python
"""
Register nodes with HaaS.

This is intended to be used as a template for either creating a mock HaaS setup
for development or to be modified to register real-life nodes that follow a
particular pattern.

In the example environment for which this module is written, there are 10
nodes which have IPMI interfaces that are sequentially numbered starting with
10.0.0.0, have a username of "ADMIN_USER" and password of "ADMIN_PASSWORD".
The ports are also numbered sequentially and are named following a dell switch
scheme, which have ports that look like "R10SW1::GI1/0/5"

It could be used in an environment similar to the one which
``haas.cfg`` corresponds, though could also be used for development with the
``haas.cfg.dev*``
"""

from subprocess import check_call

N_NODES = 6

ipmi_user = "ADMIN_USER"
ipmi_pass = "ADMIN_PASSWORD"
switch = "mock01"


def haas(*args):
    args = map(str, args)
    print args
    check_call(['haas'] + args)

haas('switch_register', switch, 'mock', 'ip', 'user', 'pass')

for node in range(N_NODES):
    ipmi_ip = "10.0.0." + str(node + 1)

    nic_port = "R10SW1::GI1/0/%d" % (node)
    nic_name = 'nic1'
    haas('node_register', node, "mock", ipmi_ip, ipmi_user, ipmi_pass)
    haas('node_register_nic', node, nic_name, 'FillThisInLater')
    haas('port_register', switch, nic_port)
    haas('port_connect_nic', switch, nic_port, node, nic_name)
