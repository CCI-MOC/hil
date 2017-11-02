#!/usr/bin/env python
"""WSGI app that helps manage pxe booting a node."""

import re
import os

from flask import Flask
app = Flask(__name__)

KS_CFG = '/var/lib/tftpboot/centos/ks.cfg'

H = r'[0-9a-fA-F]'  # hex digit
mac_regex = re.compile(r'^('+H+H+r':){5}'+H+H+r'$')


@app.route('/<mac_addr>', methods=['DELETE'])
def boot_disk(mac_addr):
    """Remove the temporary pxelinux.cfg.

    This is invoked from within ks.cfg, to avoid booting back into the
    installer on reboot.
    """
    if re.match(mac_regex, mac_addr) is None:
        return 'Bad mac address', 400

    filename = '01-' + '-'.join(mac_addr.split(':'))
    filename = filename.lower()
    os.remove('/var/lib/tftpboot/pxelinux.cfg/' + filename)
    return 'OK'


@app.route('/ks.cfg')
def kickstart():
    """Serve ks.cfg"""
    with open(KS_CFG) as f:
        return f.read()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
