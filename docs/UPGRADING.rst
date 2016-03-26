Upgrading HaaS
==============

This file describes the procedure for upgrading HaaS to a new version.

1. Read the release notes, as they may contain version-specific information.
2. Stop the HaaS services (webserver and HaaS network daemon).
3. Download and install the new version of HaaS::

     $ git clone https://github.com/cci-moc/haas
     $ python setup.py install

3. Upgrade the database::

     $ haas-admin db upgrade heads

4. Restart the HaaS services
