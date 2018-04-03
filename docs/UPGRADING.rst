Upgrading HIL
==============

This file describes the procedure for upgrading HIL to a new version.

1. Read the release notes for the particular release, below, which will cover
   any version-specific information.
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

Release Notes
-------------

0.3 (Upcoming)
++++++++++++++

* Validation checks for the configuration file have been added; be advised
  that if there were errors in your ``hil.cfg`` that were previously
  undetected you may need to fix them before the servers will start again
* The interface to the ``hil`` command line tool has changed substantially;
  If you have custom scripts that invoke it they will likely need to be
  modified.
* URLs for API calls are now prefixed with a version number, which for the
  current (unstable) API is ``v0``; you may need to update scripts and
  settings accordingly (although the HIL tools themselves should remain
  internally consistent).

Other changes, which do not require specific action when upgrading:

* All HIL APIs are now wrapped by the client library.
* Support for a new optional "maintenance pool" feature; see
  ``docs/maintenance-pool.md``.
* Some new APIs (see ``docs/rest_api.md`` for details):
  * Networking actions can now be queried to get their status.
  * When using the database auth backend, it is possible to list users.
* Updated APIs:
  * List networks now shows public networks to regular users.
  * Some switches now support public key authentication. See
    ``docs/network-drivers.md`` for details.

0.2
+++

HaaS was renamed to HIL in this release. Accordingly, there are several
changes that need to be made when upgrading:

* Since the systemd service file is created manually, the old one needs to
  manually be deleted and the new one copied in.
  * If wanting to keep the previous haas user, then the service file needs to
    be modified to reflect the different username.
* The /var/lib/haas and /etc/haas.cfg entries need to be moved (or at least
  symlinked)
* You should remove the "haas" version, since it will be a different set of
  scripts: ``pip uninstall haas``
* Re-copy hil.wsgi and update apache's wsgi.conf entry to point to it.
* Update any scripts that have env vars (like ``HAAS_ENDPOINT```) to their
  ``HIL_`` varieties.
