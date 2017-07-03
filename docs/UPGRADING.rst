Upgrading HIL
==============

This file describes the procedure for upgrading HIL to a new version.

1. Read the release notes, as they may contain version-specific information.
2. Stop the HIL services (webserver and HIL network daemon). For exmaple::

     $ systemctl stop httpd
     $ systemctl stop hil_network

3. Download and install the new version of HIL::

     $ git clone https://github.com/cci-moc/hil
     $ python setup.py install

3. Upgrade the database::

     $ hil-admin db upgrade heads

   ``heads`` indicates that HIL core and all extensions should be upgraded
   together. This is the only workflow we support, but the curious can read the
   (developer-oriented) alembic documentation for more information:

   - `<https://alembic.readthedocs.org/en/latest/>`_
   - `<https://alembic.readthedocs.org/en/latest/branches.html>`_

4. If additional extensions have been added to ``hil.cfg``, re-run ``hil-admin
   db create``, which will create any tables needed by those extensions.

   Note that removing extensions is not currently supported.

5. Restart the HIL services. e.g.::

     $ systemctl start httpd
     $ systemctl start hil_network
