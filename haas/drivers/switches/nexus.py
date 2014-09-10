# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language
# governing permissions and limitations under the License.

"""A switch driver for the Nexus 5500

Currently the driver uses telnet to connect to the switch's console; in the
long term we want to be using SNMP.
"""

import os
import pexpect
import re


from haas.dev_support import no_dry_run

from haas.drivers.driver_tools.vlan import *

@no_dry_run
def apply_networking(net_map, config):
    def set_access_vlan(port, vlan_id):
        """Set a port to access a given vlan.

        This function expects to be called while in the config prompt, and
        leaves you there when done.
        """
        console.sendline('int ethernet 1/%s' % port)
        # set it first to switch mode then to access mode:
        console.expect(r'[\r\n]+.+# ')
        console.sendline('sw')
        console.expect(r'[\r\n]+.+# ')
        console.sendline('sw mode access')
        console.expect(r'[\r\n]+.+# ')

        if vlan_id is None:
            # turn the port off
            console.sendline('no sw')
        else:
            # set the vlan:
            console.sendline('sw access vlan %s' % vlan_id)
        console.expect(r'[\r\n]+.+# ')
        # back out to config_prompt
        console.sendline('exit')
        console.expect(r'[\r\n]+.+# ')

    nexus_ip = config['ip']
    nexus_user = config['user']
    nexus_pass = config['pass']
    try:
       console = pexpect.spawn('telnet ' + nexus_ip)
       console.expect('login: ')
       console.sendline(nexus_user)
       console.expect('password: ')
       console.sendline(nexus_pass)
       console.expect(r'[\r\n]+.+# ')
       console.sendline('config terminal')
       console.expect(r'[\r\n]+.+# ')

       for port_id in net_map:
            set_access_vlan(port_id, net_map[port_id])

    except IOError as e:
        print "Connection error while connecting to the Nexus switch({0}): {1}".format(e.errno, e.strerror)
    except:
        print "Unexpected error while connecting to the Nexus switch:", sys.exc_info()[0]
        raise
        sys.Exit(1)
