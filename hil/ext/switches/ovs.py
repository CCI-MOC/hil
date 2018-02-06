"""A switch driver for OpenVswitch."""
import re
import logging
import schema
import os
import ast
import subprocess
import shlex

from hil.model import db, Switch, BigIntegerType, SwitchSession
from hil.errors import SwitchError

logger = logging.getLogger(__name__)

# Class layout
# 1. Public methods:
# 2. Private methods
# 3. Unimplemented superclass methods.


class Ovs(Switch, SwitchSession):
    """ Driver for openvswitch. """
    api_name = 'http://schema.massopencloud.org/haas/v0/switches/ovs'
    __mapper_args__ = {
        'polymorphic_identity': api_name,
    }

    id = db.Column(
            BigIntegerType, db.ForeignKey('switch.id'), primary_key=True
            )
    hostname = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    @staticmethod
    def validate(kwargs):
        """Checks input to match switch parameters."""
        schema.Schema({
            'username': basestring,
            'hostname': basestring,
            'password': basestring,
        }).validate(kwargs)

    @staticmethod
    def validate_port_name(port):
        """ This driver accepts any string as port name."""

# 1. Public Methods:

    def get_capabilities(self):
        """Provides the features of this switch that HIL supports. """
        return['Virtual_switch_for_development_Purpose_only']

    def ovs_connect(self, *command_strings):
        """Interacts with the Openvswitch.

        Args:
            *command_strings (tuple) : tuple of shell commands required 
                        to make changes to openvswitch
        Raises: SwitchError
        Returns: If successful returns None else logs error message
        """
        try:
            for command in command_strings:
                arg_list = shlex.split(command)
                subprocess.check_call(arg_list)
        except subprocess.CalledProcessError as e:
            logger.error('%s', e)
            raise SwitchError

    def get_port_networks(self, port):
        """ Provides networks connected to the given port.
        Args:
            port: Valid port name
        Returns: List of vlans assigned to the port. 
        """
        (port,) = filter(lambda p: p.label == port, self.ports)
        interface = port.label
        port_info = self._interface_info(interface)
        return port_info


    def revert_port(self, port):
        """Resets the port to the factory default.
        Args:
            port: Valid switch port

        Returns: if successful returns None else error message.
        """
        shell_cmd_1 = 'sudo ovs-vsctl del-port {port}'.format(port=port)
        shell_cmd_2 = 'sudo ovs-vsctl add-port {switch} {port}'.format(
                    switch=self.hostname, port=port
                    ) + ' vlan_mode=native-untagged'
        self.ovs_connect(shell_cmd_1, shell_cmd_2)
        
    def modify_port(self, port, channel, new_network):
        """ Changes vlan assignment to the port.

        Args:
            port: switch port in a valid format
            channel: eg 'vlan/native' or 'vlan/<vlan_id>
            new_network: vlan_id
        Returns: If successful returns None else error.
        """
        (port,) = filter(lambda p: p.label == port, self.ports)
        interface = port.label

        if channel == 'vlan/native':
            if new_network is None:
                return self._remove_native_vlan(interface)
            else:
                return self._set_native_vlan(interface, new_network)
        else:
            match = re.match(re.compile(r'vlan/(\d+)'), channel)
            assert match is not None, "HIL passed an invalid channel to the" \
                " switch!"
            vlan_id = match.groups()[0]

            if new_network is None:
                return self._remove_vlan_from_port(interface, vlan_id)
            else:
                assert new_network == vlan_id
                return self._add_vlan_to_trunk(interface, vlan_id)

# 2. Private Methods:

    def _string_to_list(self, a_string):
        """Converts a string representation of list to list.
        Args:
            a_string: list output recieved as string.
                e.g. Strings starting with '[' and ending with ']'
        Returns: object of list type.
                 Empty list is put as None.
        """
        if a_string == '[]':
            return ast.literal_eval(a_string)
        else:
            a_string = a_string.replace("[", "['").replace("]", "']")
            a_string = a_string.replace(",", "','")
            a_list = ast.literal_eval(a_string)
            a_list = [ele.strip() for ele in a_list]
            return a_list

    def _string_to_dict(self, a_string):
        """Converts a string representation of dictionary
        into a dictionary type object.

        Args:
            a_string: dictionary recieved as type string
                eg. Strings starting with '{' and ending with '}'
        Returns: Object of dictionary type.
        """
        if a_string[0] == '{}':
            a_dict = ast.literal_eval(a_string)
            return a_dict
        else:
            a_string = a_string.replace("{", "{'").replace("}", "'}")
            a_string = a_string.replace(":", "':'").replace(",", "','")
            a_dict = ast.literal_eval(a_string)
            a_dict = {k.strip(): v.strip() for k, v in a_dict.iteritems()}
            return a_dict

    def _interface_info(self, port):
        """Gets latest configuration of port from switch.

        Args:
            port: Valid port name
        Returns: configuration status of the port
        """
        shell_cmd = "sudo ovs-vsctl list port {port}".format(port=port)
        args = shlex.split(shell_cmd)
        try:
            output = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            logger.error(" %s ", e)
            raise SwitchError
        output = output.split('\n')
        output.remove('')
        i_info = dict(s.split(':') for s in output)
        i_info = {k.strip(): v.strip() for k, v in i_info.iteritems()}
        # above statement removes extra white spaces from the keys and values.
        # That is important since other calls will be querying this dictionary.
        for x in i_info.keys():
            if i_info[x][0] == "{":
                i_info[x] = self._string_to_dict(i_info[x])
            elif i_info[x][0] == "[":
                i_info[x] = self._string_to_list(i_info[x])
        return i_info
    
    def iiinterface_info(self, port): 
        """Gets latest configuration of port from switch.
            Args:
                port: Valid port name
                Returns: configuration status of the port
        """
        shell_cmd = "sudo ovs-vsctl list port {port}".format(port=port)
        args = shlex.split(shell_cmd)
        try:
            output = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            logger.error(" %s ", e)
            raise SwitchError
        output = output.split('\n')
        output.remove('')
        i_info = dict(s.split(':') for s in output)
        i_info = {k.strip(): v.strip() for k, v in i_info.iteritems()}
        for x in i_info.keys():
            if i_info[x][0] == "{":
                i_info[x] = self._string_to_dict(i_info[x])
            elif i_info[x][0] == "[":
                i_info[x] = self._string_to_list(i_info[x])
        return i_info

    def _remove_native_vlan(self, port):
        """Removes native vlan from a trunked port.
        If it is the last vlan to be removed, it disables the port and
        reverts its state to default configuration
        Args:
            port: Valid switch port
        Returns: if successful None else error message
        """
        port_info = self._interface_info(port)
        vlan_id = port_info['tag']
        shell_cmd = "sudo ovs-vsctl remove port {port} tag {vlan_id}".format(
                    port=port, vlan_id=vlan_id
                    )
        return self.ovs_connect(shell_cmd)

    def _set_native_vlan(self, port, new_network):
        """Sets native vlan for a trunked port.
        It enables the port, if it is the first vlan for the port.
        Args:
            port: valid port of switch
            new_network: vlan_id
        """
        shell_cmd = (
                "sudo ovs-vsctl set port {port} tag={netid}".format(
                        port=port, netid=new_network
                        ) + " vlan_mode=native-untagged"
                    )

        return self.ovs_connect(shell_cmd)

    def _add_vlan_to_trunk(self, port, vlan_id):
        """ Adds vlans to a trunk port. """
        import pdb; pdb.set_trace()
        port_info = self._interface_info(port)

        if port_info['trunks'] is None:
            shell_cmd = "sudo ovs-vsctl set port {port} trunks={vlans}".format(
                    port=port, vlans=vlan_id
                    )
        else:
            all_trunks = ','.join(port_info['trunks'])+','+vlan_id
            shell_cmd = "sudo ovs-vsctl set port {port} trunks={vlans}".format(
                        port=port, vlans=all_trunks
                        )

        return self.ovs_connect(shell_cmd)

    def _remove_vlan_from_port(self, port, vlan_id):
        """ removes a single vlan specified by `vlan_id` """
        port_info = self._interface_info(port)
        shell_cmd = "sudo ovs-vsctl remove port {port} trunks {vlan}".format(
                      port=port, vlan=vlan_id
                      )
        if port_info['trunks'] is not None:
            return self.ovs_connect(shell_cmd)
        return None

# 3. superclass methods (Not Required):

    @staticmethod
    def validate_port_name(port):
        """This driver accepts any string as a port name. """

    def session(self):
        return self

    def disconnect(self):
        return self
