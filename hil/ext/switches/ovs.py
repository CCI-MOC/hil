"""A switch driver for OpenVswitch."""
import re
import logging
import schema
import subprocess

from hil.model import db, Switch, Port, BigIntegerType, SwitchSession
from hil.errors import SwitchError
from hil.ext.switches.common import string_to_dict, string_to_list

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
    ovs_bridge = db.Column(db.String, nullable=False)

    @staticmethod
    def validate(kwargs):
        """Checks input to match switch parameters."""
        schema.Schema({
            'ovs_bridge': basestring,
        }).validate(kwargs)

# 1. Public Methods:

    def get_capabilities(self):
        return ['nativeless-trunk-mode']

    def ovs_connect(self, *command_strings):
        """Interacts with the Openvswitch.

        Args:
            *command_strings (tuple) : tuple of list of arguments required
                        to make changes to openvswitch
        Raises: SwitchError
        Returns: If successful returns None else logs error message
        """
        try:
            for arg_list in command_strings:
                subprocess.check_call(arg_list)
        except subprocess.CalledProcessError as e:
            logger.error('%s', e)
            raise SwitchError('ovs command failed: %s', e)

    def get_port_networks(self, ports):

        response = {}
        for port in ports:
            trunk_id_list = self._interface_info(port.label)['trunks']
            if trunk_id_list == []:
                response[port] = []
            else:
                result = []
                for trunk in trunk_id_list:
                    name = "vlan/"+trunk
                    result.append((name, trunk))
                response[port] = result
            native = self._interface_info(port.label)['tag']
            if native != []:
                response[port].append(("vlan/native", native))

        return response

    def revert_port(self, port):

        args_1 = ['sudo', 'ovs-vsctl', 'del-port', str(port)]
        args_2 = [
                'sudo', 'ovs-vsctl', 'add-port', str(self.ovs_bridge),
                str(port), 'vlan_mode=native-untagged'
                ]
        self.ovs_connect(args_1, args_2)

    def modify_port(self, port, channel, new_network):

        port_obj = Port.query.filter_by(label=port).one()
        interface = port_obj.label

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

    def _interface_info(self, port):
        """Gets latest configuration of port from switch.

        Args:
            port: Valid port name
        Returns intermediate output which processed to return final output:
        It is a string of the following format:
        '_uuid               : ad489368-9b53-4a3e-8732-697ad5141de9\n
        bond_downdelay      : 0\nbon    d_fake_iface     : false\n
        external_ids        : {}\nfake_bridge         : false\n
        interfaces              : [fc61c8ff99c5,fc61c8ff99c6]\n
        name                : "veth-0"\n
        statistics          : {abc:123    , def:xyz,  space  :  lot of it , \
                2345:some number}\n
        status              : {}\ntag                     : 100\n
        trunks              : [200,300,400]\n
        vlan_mode           : native-untagged\n'

        Which is used as input for further processing.
        Returns: A dictionary of configuration status of the port.
             String, Dictionary and list are valid values of this dictionary.
             eg: Sample output.
               {
                '_uuid': 'ad489368-9b53-4a3e-8732-697ad5141de9',
                'bond_downdelay': '0',
                'bond_fake_iface': 'false',
                'external_ids': {},
                'fake_bridge': 'false',
                'interfaces': ['fc61c8ff99c5', 'fc61c8ff99c6'],
                'name': '"veth-0"',
                'statistics': {'2345': 'some number','abc': '123','def': 'xyz'
                                ,'space': 'lot of it'},
                'status': {},
                'tag': '100',
                'trunks': ['200', '300', '400'],
                'vlan_mode': 'native-untagged'
              }
        """
        # This function is differnet then `ovs_connect` as it uses
        # subprocess.check_output because it only needs read info from switch
        # and pass the output to calling funtion.
        args = ['sudo', 'ovs-vsctl', 'list', 'port', str(port)]
        try:
            output = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            logger.error(" %s ", e)
            raise SwitchError('Ovs command failed: %s', e)
        output = output.split('\n')
        output.remove('')
        i_info = dict(s.split(':', 1) for s in output)
        i_info = {k.strip(): v.strip() for k, v in i_info.iteritems()}
        for x in i_info.keys():
            if i_info[x][0] == "{":
                i_info[x] = string_to_dict(i_info[x])
            elif i_info[x][0] == "[":
                i_info[x] = string_to_list(i_info[x])
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
        args = [
                'sudo', 'ovs-vsctl', 'remove', 'port', str(port), 'tag',
                str(vlan_id)
                ]
        return self.ovs_connect(args)

    def _set_native_vlan(self, port, new_network):
        """Sets native vlan for a trunked port.
        It enables the port, if it is the first vlan for the port.
        Args:
            port: valid port of switch
            new_network: vlan_id
        """
        args = [
                'sudo', 'ovs-vsctl', 'set', 'port', str(port),
                'tag='+str(new_network), 'vlan_mode=native-untagged'
                ]

        return self.ovs_connect(args)

    def _add_vlan_to_trunk(self, port, vlan_id):
        """ Adds vlans to a trunk port. """
        port_info = self._interface_info(port)

        if not port_info['trunks']:
            args = [
                    'sudo', 'ovs-vsctl', 'set', 'port', str(port),
                    'trunks='+str(vlan_id)
                    ]
        else:
            all_trunks = ','.join(port_info['trunks'])+','+vlan_id
            args = [
                    'sudo', 'ovs-vsctl', 'set', 'port', str(port),
                    'trunks='+str(all_trunks)
                    ]

        return self.ovs_connect(args)

    def _remove_vlan_from_port(self, port, vlan_id):
        """ removes a single vlan specified by `vlan_id` """
        port_info = self._interface_info(port)
        args = [
                'sudo', 'ovs-vsctl', 'remove', 'port', str(port), 'trunks',
                str(vlan_id)
                ]
        if port_info['trunks']:
            return self.ovs_connect(args)
        return None

# 3. Other superclass methods:

    @staticmethod
    def validate_port_name(port):
        """This driver accepts any string as a port name. """

    def session(self):
        return self

    def disconnect(self):
        pass
