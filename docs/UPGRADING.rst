Upgrading HaaS
==============

This file describes the procedure for upgrading HaaS to a new version.

1. Read the release notes, as they may contain version-specific information.
2. Stop the HaaS services (webserver and HaaS network daemon). For exmaple::

     $ systemctl stop httpd
     $ systemctl stop haas_network

3. Download and install the new version of HaaS::

     $ git clone https://github.com/cci-moc/haas
     $ python setup.py install

3. Upgrade the database::

     $ haas-admin db upgrade heads

4. If additional extensions have been added to ``haas.cfg``, re-run ``haas-admin
   db create``, which will create any tables needed by those extensions.

5. Restart the HaaS services. e.g.::

     $ systemctl start httpd
     $ systemctl start haas_network
