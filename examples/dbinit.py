#!/usr/bin/python
"""
Register nodes with HIL.

This is intended to be used as a template for either creating a mock HIL setup
for development or to be modified to register real-life nodes that follow a
particular pattern.

In the example environment for which this module is written, there are 10
nodes which have IPMI interfaces that are sequentially numbered starting with
10.0.0.0, have a username of "ADMIN_USER" and password of "ADMIN_PASSWORD".
The ports are also numbered sequentially and are named following a dell switch
scheme, which have ports that look like "gi1/0/5"

It could be used in an environment similar to the one which
``hil.cfg`` corresponds, though could also be used for development with the
``hil.cfg.dev*``
"""

from subprocess import check_call

N_NODES = 6

ipmi_user = "ADMIN_USER"
ipmi_pass = "ADMIN_PASSWORD"
switch = "mock01"


def hil(*args):
    """Convenience function that calls the hil command line tool with
    the given arguments.
    """
    args = map(str, args)
    print args
    check_call(['hil'] + args)

hil('switch_register', switch, 'mock', 'ip', 'user', 'pass')

for node in range(N_NODES):
    ipmi_ip = "10.0.0." + str(node + 1)

    nic_port = "gi1/0/%d" % (node)
    nic_name = 'nic1'
    hil('node_register', node, "mock", ipmi_ip, ipmi_user, ipmi_pass)
    hil('node_register_nic', node, nic_name, 'FillThisInLater')
    hil('port_register', switch, nic_port)
    hil('port_connect_nic', switch, nic_port, node, nic_name)
