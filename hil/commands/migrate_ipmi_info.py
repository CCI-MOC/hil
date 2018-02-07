"""Helper commands for moving IPMI info from the database to obmd.

This is part of our obmd migration strategy; see the discussion at:


"""
import sys
import json

import requests

from flask_script import Command, Option

from hil import server
from hil.flaskapp import app
from hil import model


class MigrateIpmiInfo(Command):
    """Migrate ipmi info to obmd"""

    option_list = (
        Option('--obmd-base-url', dest='obmd_base_url',
               help='Base url for the obmd api'),
        Option('--obmd-admin-token', dest='obmd_admin_token',
               help='Admin token for obmd'),
    )

    def run(self, obmd_base_url, obmd_admin_token):
        server.init()
        with app.app_context():
            info = db_extract_ipmi_info()
            obmd_upload_ipmi_info(obmd_base_url, obmd_admin_token, info)
            db_add_obmd_info(obmd_base_url, obmd_admin_token)


def db_extract_ipmi_info():
    """Extract all nodes' ipmi connection info from the database.

    This returns an dictionary of the form:

        {
            "node-23": {
                "host": "172.16.32.23",
                "user": "admin",
                "password": "secret"
            },
            "node-46": {
                "host": "172.16.32.46",
                "user": "admin",
                "password": "changeme"
            }
        }

    It will fail if any of the nodes in the database have obms with a type
    other than ipmi.

    This must be run inside of an app context.
    """
    obms = model.Obm.query.all()

    info = {}

    ipmi_api_name = 'http://schema.massopencloud.org/haas/v0/obm/ipmi'

    for obm in obms:
        # XXX: apparently we've incorrectly specified the relationship between
        # Obms and nodes, such that the node attribute returns a list, even
        # though there can only ever be one node. If we were keeping pluggable
        # obm support for longer, We'd just fix this, but since we're removing
        # the functionality soon it's easier to just do this and not have to
        # worry about what other code we might disturb:
        node = obm.node[0]

        if obm.type != ipmi_api_name:
            sys.exit(("Node %s{label} has an obm of unspported "
                      "type %s{type}").format({
                          'label': node.label,
                          'type': obm.type,
                      }))
        info[node.label] = {
            'host': obm.host,
            'user': obm.user,
            'password': obm.password,
        }

    return info


def obmd_upload_ipmi_info(obmd_base_url, obmd_admin_token, info):
    """Upload nodes' info to obmd.

    `info` should be a dictionary of the form returned by
    `db_extract_ipmi_info`.

    `obmd_base_url` is the base URL for the obmd api. i.e. a node named
    "example_node" would be at the URL `obmd_base_url + '/node/example_node'.`

    `obmd_admin_token` is the admin token to use when authenticating against
    obmd.
    """
    sess = requests.Session()
    sess.auth = ('admin', obmd_admin_token)

    for key, val in info.items():
        sess.put(obmd_base_url + '/node/' + key, data=json.dumps({
            'type': 'ipmi',
            'info': {
                'addr': val['host'],
                'user': val['user'],
                'pass': val['password'],
            },
        }))


def db_add_obmd_info(obmd_base_url, obmd_admin_token):
    """Add obmd connection info to the HIL database.

    This assumes each node is available from obmd at the URL
    `obmd_base_url + '/node/' + node.label`.

    This must be run inside of an app context.
    """
    model.Node.query.update({'obmd_admin_token': obmd_admin_token})
    for node in model.Node.query.all():
        node.obmd_uri = obmd_base_url + '/node/' + node.label
    model.db.session.commit()
