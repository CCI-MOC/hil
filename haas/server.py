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


@app.route('/hnic/<hnicname>', methods=['PUT', 'DELETE'])
@api_function
def hnic(hnicname):
    """Handle create/delete hnic commands."""
    if request.method == 'PUT':
        return api.headnode_create_hnic(request.form['headnode'],
                                        hnicname,
                                        request.form['macaddr'])
    else: # DELETE
        return api.headnode_delete_hnic(hnicname)


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


@app.route('/project/<projectname>/connect_node', methods=['POST'])
@api_function
def project_connect_node(projectname):
    return api.project_connect_node(projectname, request.form['node'])

@app.route('/project/<projectname>/detach_node', methods=['POST'])
@api_function
def project_detach_node(projectname):
    return api.project_detach_node(projectname, request.form['node'])


if __name__ == '__main__':
    config.load()
    model.init_db(create=True)
    app.run(debug=True)
