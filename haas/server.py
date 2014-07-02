"""This is the HaaS API server - it provides the HaaS's rest api.

This module only marshalls between HTTP and the routines in haas.api; it doesn't
directly ipmlement the semantics of the API.

To start the server, invoke `haas serve` from the command line.
"""

from flask import Flask, request
from haas import config, model, api


def api_function(f):
    """A decorator which adds some error handling.

    If the function decorated with `api_function` raises an exception of type
    `api.APIError`, the error will be reported to the client, whereas other
    exceptions (being indications of a bug in the HaaS) will not be.
    """
    def wrapped(*args, **kwargs):
        try:
            resp = f(*args, **kwargs)
        except api.APIError as e:
            # Right now we're always returning 400 (Bad Request). This probably
            # isn't actually the right thing to do.
            #
            # Additionally, we're getting deprecation errors about the use of
            # the message attribute. TODO: figure out what the right way to do
            # this is.
            return e.message, 400
        if not resp:
            return ''
    wrapped.__name__ = f.__name__
    return wrapped



app = Flask(__name__)


@app.route('/user/<username>', methods=['PUT', 'DELETE'])
@api_function
def user(username):
    """Handle create/delete user commands."""
    if request.method == 'PUT':
        return api.user_create(username, request.form['password'])
    else: # DELETE
        return api.user_delete(username)


@app.route('/node/<nodename>', methods=['PUT'])
@api_function
def node_register(nodename):
    return api.node_register(nodename)

@app.route('/node/<nodename>/nic/<nicname>', methods=['PUT', 'DELETE'])
@api_function
def nic(nodename, nicname):
    """Handle create/delete nic commands."""
    if request.method == 'PUT':
        return api.node_register_nic(nodename,
                                     nicname,
                                     request.form['macaddr'])
    else: # DELETE
        return api.node_delete_nic(nodename,
                                   nicname)

@app.route('/project/<projectname>', methods=['PUT', 'DELETE'])
@api_function
def project(projectname):
    """Handle create/delete project commands."""
    if request.method == 'PUT':
        return api.project_create(projectname, request.form['group'])
    else: # DELETE
        return api.project_delete(projectname)

@app.route('/project/<projectname>/deploy', methods=['POST'])
@api_function
def project_deploy(projectname):
    api.project_deploy(projectname)


@app.route('/headnode/<name>', methods=['PUT', 'DELETE'])
@api_function
def headnode(name):
    if request.method == 'PUT':
        return api.headnode_create(name, request.form['group'])
    else: # DELETE
        return api.headnode_delete(name)


@app.route('/headnode/<headnodename>/hnic/<hnicname>', methods=['PUT', 'DELETE'])
@api_function
def hnic(headnodename, hnicname):
    """Handle create/delete hnic commands."""
    if request.method == 'PUT':
        return api.headnode_create_hnic(headnodename,
                                        hnicname,
                                        request.form['macaddr'])
    else: # DELETE
        return api.headnode_delete_hnic(headnodename,
                                        hnicname)


@app.route('/group/<groupname>', methods=['PUT', 'DELETE'])
@api_function
def group(groupname):
    """Handle create/delete group commands."""
    if request.method == 'PUT':
        return api.group_create(groupname)
    else: # DELETE
        return api.group_delete(groupname)    


@app.route('/group/<groupname>/add_user', methods=['POST'])
@api_function
def group_add_user(groupname):
    return api.group_add_user(groupname, request.form['user'])


@app.route('/group/<groupname>/remove_user', methods=['POST'])
@api_function
def group_remove_user(groupname):
    return api.group_remove_user(groupname, request.form['user'])

@app.route('/switch/<switchname>', methods=['PUT', 'DELETE'])
@api_function
def switch(switchname):
    if request.method == 'PUT':
        return api.switch_register(switchname, request.form['driver'])
    else: # DELETE
        return api.switch_delete(switchname)

@app.route('/switch/<switch>/port/<port>', methods=['PUT', 'DELETE'])
@api_function
def port(switch, port):
    if request.method == 'PUT':
        return api.port_register(switch, port)
    else: # DELETE
        return api.port_delete(switch, port)

@app.route('/switch/<switch>/port/<port>/connect_nic', methods=['POST'])
@api_function
def port_connect_nic(switch, port):
    return api.port_connect_nic(switch,
                                port,
                                request.form['node'],
                                request.form['nic'])

@app.route('/switch/<switch>/port/<port>/detach_nic', methods=['POST'])
@api_function
def port_detach_nic(switch, port):
    return api.port_detach_nic(switch, port)

@app.route('/network/<networkname>', methods=['PUT', 'DELETE'])
@api_function
def network(networkname):
    """Handle create/delete network commands."""
    if request.method == 'PUT':
        return api.network_create(networkname, request.form['group'])
    else: # DELETE
        return api.network_delete(networkname)

@app.route('/project/<projectname>/connect_node', methods=['POST'])
@api_function
def project_connect_node(projectname):
    return api.project_connect_node(projectname, request.form['node'])

@app.route('/project/<projectname>/detach_node', methods=['POST'])
@api_function
def project_detach_node(projectname):
    return api.project_detach_node(projectname, request.form['node'])

@app.route('/project/<projectname>/connect_headnode', methods=['POST'])
@api_function
def project_connect_headnode(projectname):
    return api.project_connect_headnode(projectname, request.form['headnode'])

@app.route('/project/<projectname>/detach_headnode', methods=['POST'])
@api_function
def project_detach_headnode(projectname):
    return api.project_detach_headnode(projectname, request.form['headnode'])

@app.route('/project/<projectname>/connect_network', methods=['POST'])
@api_function
def project_connect_network(projectname):
    return api.project_connect_network(projectname, request.form['network'])

@app.route('/project/<projectname>/detach_network', methods=['POST'])
@api_function
def project_detach_network(projectname):
    return api.project_detach_network(projectname, request.form['network'])


@app.route('/node/<node>/nic/<nic>/connect_network', methods=['POST'])
@api_function
def node_connect_network(node, nic):
    return api.node_connect_network(node, nic, request.form['network'])

@app.route('/node/<node>/nic/<nic>/detach_network', methods=['POST'])
@api_function
def node_detach_network(node, nic):
    return api.node_detach_network(node, nic)

@app.route('/headnode/<headnode>/hnic/<hnic>/connect_network', methods=['POST'])
@api_function
def headnode_connect_network(headnode, hnic):
    return api.headnode_connect_network(headnode, hnic, request.form['network'])

@app.route('/headnode/<headnode>/hnic/<hnic>/detach_network', methods=['POST'])
@api_function
def headnode_detach_network(headnode, hnic):
    return api.headnode_detach_network(headnode, hnic)




@app.route('/vlan/<vlan_id>', methods=['PUT', 'DELETE'])
@api_function
def vlan(vlan_id):
    """Handle register/delete vlan commands."""
    if request.method == 'PUT':
        return api.vlan_register(vlan_id)
    else: # DELETE
        return api.vlan_delete(vlan_id)


if __name__ == '__main__':
    config.load()
    model.init_db(create=True)
    app.run(debug=True)
