"""Helper command for extracting IPMI info from the database.

This is part of our obmd migration strategy; the idea is that this
information is then uploaded to obmd.
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

    This prints a json object of the form:

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

    It will fail if any of the
    """
    obms = model.Obm.query.all()

    info = {}

    for obm in obms:
        if obm.type != 'ipmi':
            sys.exit(("Node %s{label} has an obm of unspported "
                      "type %s{type}").format({
                          'label': obm.owner.label,
                          'type': obm.type,
                      }))
        info[obm.owner.label] = {
            'host': obm.host,
            'user': obm.user,
            'password': obm.password,
        }

    return info


def obmd_upload_ipmi_info(obmd_base_url, obmd_admin_token, info):
    """Upload nodes' info to obmd.

    The info is loaded from stdin, and should be in the format output
    by `extract_ipmi_info`.
    """
    info = json.load(sys.stdin)

    sess = requests.Session(auth=('admin', obmd_admin_token))

    # TODO: validate the input.

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
    model.Node.query.update({'obmd_admin_token': obmd_admin_token})
    for node in model.Node.query.all():
        node.obmd_uri = obmd_base_url + '/node/' + node.label
    model.db.commit()
