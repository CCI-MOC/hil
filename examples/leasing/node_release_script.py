#! /bin/python
"""
This script will free nodes from a project after
a specific amount of time.
Script reads a config file from /etc/leasing.cfg
which defines which nodes are in the project, time threshold
admin user name and password and status file.

status file includes each nodes status. which node is in
the project, which one is free and for how long the node
has been in the project.
"""

from sets import Set
import time
import ConfigParser
from os import remove
from shutil import move

from hil.client.client import Client, RequestsHTTPClient
from hil.client.base import FailedAPICallException


class HILClientFailure(Exception):
    """Exception indicating that the HIL client failed"""


def hil_client_connect(endpoint_ip, name, pw):
    """Connect to the HIL server and return a HIL Client instance"""

    hil_http_client = RequestsHTTPClient()
    if not hil_http_client:
        print('Unable to create HIL HTTP Client')
        return None

    hil_http_client.auth = (name, pw)

    return Client(endpoint_ip, hil_http_client)


def release_nodes(
        statusfile, non_persistent_list,
        threshold_time, hil_username, hil_password, hil_endpoint,
        hil_client=None
        ):

    """Release nodes : Takes node list as arguments
    and puts them back to free pool after given time"""

    if not hil_client:
        hil_client = hil_client_connect(
                        hil_endpoint, hil_username, hil_password)

    free_node_list = hil_client.node.list('free')
    # Only these nodes should be updated in
    # the file(either for project or for time)
    nodes_to_update_infile = list(Set(
        non_persistent_list)-Set(free_node_list))

    for node in nodes_to_update_infile:
        # get the information from status file for node.
        node_info_from_file = get_project_and_time_for_node(statusfile, node)
        project_in_file = node_info_from_file[0]
        old_time = node_info_from_file[1]

        # get the information from HIL for node
        node_current_info = hil_client.node.show(node)
        project_in_hil = node_current_info['project']
        # Increase the time by one unit
        new_time = int(node_info_from_file[1])+1
        # See if the node is in the same project and if it is outside
        # free pool for time less than threshold value then update only
        # time in status file
        if (project_in_file == project_in_hil and
                new_time < threshold_time):
            update_time_for_node(statusfile, node, old_time, new_time)
        # See if the node is in the same project and if it is outside
        # free pool for time greater than threshold value then release
        # the node back to free pool
        elif (project_in_file == project_in_hil and
                new_time >= threshold_time):
            # Detaching nodes from networks
            detach_networks_from_node(hil_client, node)
            # Releasing node from project.
            release_from_project(hil_client, statusfile, node, project_in_hil)

        # See if the node is not in free pool and check if the projects
        # are not matching then we need to update project in status file
        elif (project_in_file != project_in_hil and
                project_in_hil is not None):
            update_project_in_status_file(
                statusfile, node, project_in_hil,
                project_in_file)


def get_project_and_time_for_node(statusfile, node):
    """Reads current information from file for every node."""

    node_status = ''
    node_project = ''
    node_duration = 0
    with open(statusfile, 'r') as status_file:
        for line in status_file:
            node_status = line.split()
            if node == node_status[0]:
                node_project = node_status[1]
                node_duration = node_status[2]
    status_file.close()
    return (node_project, node_duration)


def update_time_for_node(
        statusfile, node,
        old_time, new_time
        ):
    """Updates the time for a node in file"""

    newline = ''
    with open(statusfile, 'r') as status_file,\
            open('/tmp/tempfile', 'w') as output_file:
        for line in status_file:
            words = line.split()
            if node == words[0]:
                words[2] = str(new_time)
                newline = ' '.join(words)+"\n"
                output_file.write(newline)
            else:
                output_file.write(line)
    status_file.close()
    output_file.close()

    remove(statusfile)
    move('/tmp/tempfile', statusfile)


def update_project_in_status_file(
        statusfile, node, new_project, old_project
        ):
    """Project will be changed in
    file to match the project in HIL"""

    newline = ''
    with open(statusfile, 'r') as status_file,\
            open('/tmp/tempfile', 'w') as output_file:
        for line in status_file:
            words = line.split()
            if node == words[0]:
                words[1] = new_project
                newline = ' '.join(words) + "\n"
                output_file.write(newline)
            else:
                output_file.write(line)
    status_file.close()
    output_file.close()
    remove(statusfile)
    move('/tmp/tempfile', statusfile)


def detach_networks_from_node(hil_client, node):
    """Disconnect all networks from all of the node's NICs
    get node information and then iterate on the nics"""

    node_info = hil_client.node.show(node)

    for nic in node_info['nics']:
        # get the port and switch to which the nics are connected to
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


def release_from_project(
        hil_client, statusfile, node, project
        ):
    """Updates the file with project name as free and
    releases it back to free pool"""

    time.sleep(2)
    # tries 2 times to detach the project because there might be a pending
    # networking action setup by revert port in the previous step.
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

    with open(statusfile, 'r') as status_file, \
            open('/tmp/tempfile', 'w') as output_file:
        for line in status_file:
            words = line.split()
            if node == words[0]:
                newline = node + " " + "free_pool " + str(0) + "\n"
                output_file.write(newline)
            else:
                output_file.write(line)
    status_file.close()
    output_file.close()
    remove(statusfile)
    move('/tmp/tempfile', statusfile)

if __name__ == "__main__":
    try:
        config = ConfigParser.SafeConfigParser()
        config.read("/etc/leasing.cfg")
        node_list = [x.strip()
                     for x in config.get('hil', 'node_list').split(',')]
        threshold = int(config.get('hil', 'threshold'))
        hil_url = config.get('hil', 'url')

        hil_username = config.get('hil', 'user_name')
        hil_password = config.get('hil', 'password')
        hil_endpoint = config.get('hil', 'endpoint')

        statusfile = config.get('hil', 'status_file')
        release_nodes(
            statusfile, node_list, threshold,
            hil_username, hil_password, hil_endpoint
            )
    except ConfigParser.NoOptionError, err:
        print err
