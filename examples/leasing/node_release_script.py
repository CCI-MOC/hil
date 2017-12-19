#! /bin/python
"""
This script will free nodes from a project after
a specific amount of time.

You can find more information including
config file and status file format in
README file.
"""

import time
import ConfigParser

from hil.client.client import Client, RequestsHTTPClient
from hil.client.base import FailedAPICallException


class HILClientFailure(Exception):
    """Exception indicating that the HIL client failed"""


class StatusFileError(Exception):
    """Exception regarding Status File Format"""


def hil_client_connect(endpoint_ip, name, pw):
    """Returns a HIL client object"""

    hil_http_client = RequestsHTTPClient()
    hil_http_client.auth = (name, pw)

    return Client(endpoint_ip, hil_http_client)


def load_node_info(statusfile):
    """
    Creates a structure containing all information from the
    file. We will change and update this data structure and then
    write it back to the file. In this way, the file will be read
    and written once.
    """
    nodes = {}
    with open(statusfile, 'r') as status_file:
        for line in status_file:
            node_status = line.split()
            nodes[node_status[0]] = {}
            nodes[node_status[0]].update({'project': node_status[1],
                                          'time': node_status[2]})
    return nodes


def release_from_project(
        hil_client, node, project
        ):
    """
    We need to disconnect all the networks from all of the node's NICs
    before releasing the node, after that we can detach node from
    the project
    """

    node_info = hil_client.node.show(node)

    for nic in node_info['nics']:
        port = nic['port']
        switch = nic['switch']
        if port and switch:
            try:
                hil_client.port.port_revert(switch, port)
                print('Removed all networks from node `%s`' % node)
            except FailedAPICallException:
                print('Failed to revert port `%s` on node \
                        `%s` switch `%s`' % (port, node, switch))
                raise HILClientFailure()

    time.sleep(5)
    # tries 2 times to detach the project because there might be a pending
    # networking action setup (revert port in the previous step).
    counter = 2
    while counter:

        try:
            hil_client.project.detach(project, node)
            print('Node `%s` removed from project `%s`' % (node, project))
            break
        except FailedAPICallException as ex:
            if ex.message == 'Node has pending network actions':
                counter -= 1
                time.sleep(2)
            else:
                print('HIL reservation failure: Unable to \
                        detach node `%s` from project `%s`' % (node, project))
                raise HILClientFailure(ex.message)
    if counter == 0:
        print('HIL reservation failure: Unable to detach node \
                `%s` from project `%s`' % (node, project))
        raise HILClientFailure()


def update_file(statusfile, nodes):
    """
    Writing the updated data structure's info back to the file.
    """

    with open(statusfile, 'w') as status_file:
        for node in sorted(nodes):
            status_file.write(str(node) + ' ' + str(nodes[node]['project']) +
                              ' ' + str(nodes[node]['time']) + '\n')


def release_nodes(
        statusfile, non_persistent_list,
        threshold_time, hil_username, hil_password, hil_endpoint,
        hil_client=None
        ):

    """Release nodes : After certain amount of time (threshold),
    we should return the nodes back to the free pool.
    Tenants who need more time should ask time extension.
    """

    if not hil_client:
        hil_client = hil_client_connect(
                        hil_endpoint, hil_username, hil_password)

    free_node_list = hil_client.node.list('free')
    # Only these nodes should be updated in
    # the file(either for project or for time)
    nodes_to_update = list(set(
        non_persistent_list)-set(free_node_list))

    # All nodes should have information in status file
    nodes = load_node_info(statusfile)

    for node in nodes_to_update:
        if nodes[node] is None:
            print('Information of node %s \
                    is missing in the status file' % (node))
            raise StatusFileError()
        project = nodes[node]['project']
        time = nodes[node]['time']

        node_current_info = hil_client.node.show(node)
        project_in_hil = node_current_info['project']
        new_time = int(time)+1
        # Just update the time for the nodes which have been in
        # the project for less than the threshold
        if (project == project_in_hil and
                new_time < threshold_time):
            nodes[node]['time'] = new_time
        # If the time of the node is passed the threshold,
        # release it from the project
        elif (project == project_in_hil and
                new_time >= threshold_time):
            release_from_project(hil_client, node, project_in_hil)
            nodes[node]['project'] = 'free_pool'
            nodes[node]['time'] = '0'

        # There is a mistmatch in the status file and actual status.
        # The file should be updated.
        # This covers the edge case when someone releases the node
        # and the node is assigned to another project.
        elif (project != project_in_hil and
                project_in_hil is not None):
            nodes[node]['project'] = project_in_hil
            nodes[node]['time'] = '1'

    update_file(statusfile, nodes)


if __name__ == "__main__":
    try:
        config = ConfigParser.SafeConfigParser()
        config.read("/etc/leasing.cfg")
        node_list = [x.strip()
                     for x in config.get('hil', 'node_list').split(',')]

        release_nodes(
            config.get('hil', 'status_file'),
            node_list,
            int(config.get('hil', 'threshold')),
            config.get('hil', 'user_name'),
            config.get('hil', 'password'),
            config.get('hil', 'endpoint')
            )

    except ConfigParser.NoOptionError, err:
        print err
