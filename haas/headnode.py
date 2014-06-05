"""This module provides routines for managing head nodes.

The exact API is currently in flux; We will attempt to make sure that
any given time the docstrings are accurate, but make no promises about
what it will say tomorrow.

Not everything is implemented to spec (or sometimes at all). Things
which are not are labeld as such (typically under the heading
"Conformance issues").
"""

import uuid
from subprocess import check_call as cmd
from haas.config import cfg

class HeadNode(object):
    """A head node virtual machine.

    Conformance issues:
    - The network interface stuff is currently unimplemented.
    """

    def __init__(self, name):
        """Clients of this module should *not* call this method directly.

        Instead, create a `Connection` and call `make_headnode()`.
        """
        self.name = name
        self.nics = []

    def stop(self):
        """Stop the vm.

        This does a hard poweroff; the OS is not given a chance to react.
        """
        cmd(['virsh', 'destroy', self.name])

    def add_nic(self, vlan_id):
        trunk_nic = cfg.get('headnode', 'trunk_nic')
        bridge = 'br-vlan%d' % vlan_id
        vlan_nic = '%s.%d' % (trunk_nic, vlan_id)
        vlan_id = str(vlan_id)
        cmd(['brctl', 'addbr', bridge])
        cmd(['vconfig', 'add', trunk_nic, vlan_id])
        cmd(['brctl', 'addif', bridge, vlan_nic])
        cmd(['ifconfig', bridge, 'up', 'promisc'])
        cmd(['ifconfig', vlan_nic, 'up', 'promisc'])
        cmd(['virsh', 'attach-interface', self.name, 'bridge', bridge, '--config'])
        self.nics.append(vlan_id)

    def delete(self):
        """Delete the vm, including associated storage"""
        trunk_nic = cfg.get('headnode', 'trunk_nic')
        cmd(['virsh', 'undefine', self.name, '--remove-all-storage'])
        for nic in self.nics:
            nic = str(nic)
            bridge = 'br-vlan%s' % nic
            vlan_nic = '%s.%d' % (trunk_nic, nic)
            cmd(['ifconfig', bridge, 'down'])
            cmd(['ifconfig', vlan_nic, 'down'])
            cmd(['brctl', 'delif', bridge, vlan_nic])
            cmd(['vconfig', 'rem', vlan_nic])
            cmd(['brctl', 'delbr', bridge])

    def get_interfaces(self):
        """Return a list of the vm's network interfaces.

        The members of the list will be instances of `Interface`. the
        index of each interface reflects the order of the interfaces as
        seen by the vm, i.e. (typically, though it depends on the guest),
        in interfaces list ints, ints[0] will be eth0, ints[1] will be
        eth1, and so on.

        Modification of this list *will not* affect the vm in any way;
        to update the configuration, use `set_interfaces`.
        """
        pass

    def set_interfaces(self, interfaces):
        """Set the vm's list of nics to `interfaces`.

        This will overwrite any previous network configuration. Any
        previously existing nics that are not in the list will be
        removed. If the vm is running, changes will not take effect
        until it is restarted.

        The argument to this function has the same semantics as the
        return value of `get_interfaces`.
        """
        pass


class Interface(object):
    """One of a virtual machine's network interface cards."""

    def __init__(self, vlan_id):
        """Create a new nic attached to vlan #vlan_id.

        The nic is an immutable object - once created it cannot be
        modified. Instead, a user wishing to reconfigure a vm should
        remove this interface and add a new one.
        """
        self.vlan_id = vlan_id

    def get_vlan(self):
        """Return the vlan number associated with this network card."""
        return self.vlan_id
