# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

"""Deployment Unit test"""

from haas import api
from haas.test_common import *

class TestHeadNodeCreate:

    @deployment_test
    @hnic_cleanup
    def test_headnode_start(self, db):
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.network_create('spider-web', 'anvil-nextgen')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hnic-0', 'de:ad:be:ef:20:14')
        api.headnode_connect_network('hn-0', 'hnic-0', 'spider-web')
        api.headnode_start('hn-0')
        #api.headnode_stop('hn-0')
        #api.headnode_delete('hn-0')

    
