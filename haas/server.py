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


@app.route('/project/<projectname>/deploy', methods=['POST'])
@api_function
def project_deploy(projectname):
    api.project_deploy(projectname)

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

@app.route('/group/<groupname>/add_user', methods=['POST'])
@api_function
def group_add_user(groupname):
    return api.group_add_user(groupname, request.form['user'])


@app.route('/group/<groupname>/remove_user', methods=['POST'])
@api_function
def group_remove_user(groupname):
    return api.group_remove_user(groupname, request.form['user'])


if __name__ == '__main__':
    config.load()
    model.init_db(create=True)
    app.run(debug=True)
