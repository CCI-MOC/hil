# Keystone Authentication

An authentication backend for Openstack's Keystone is maintained in this
source tree as `hil.ext.auth.keystone`. This document describes its
configuration and usage in detail.

NOTE: The HIL command line interface only supports the Keystone v3 API.
The server supports anything supported by [keystonemiddleware][1].

## Usage

Once HIL has been configured to work with Keystone, an administrator
must manually add Openstack projects to HIL before they can access the
HIL API. The HIL project names must correspond to the Openstack UUIDs.
For example, an administrator may execute the command:

    hil project_create 00de7c85e594473db7461cdf7367166a

To grant the Openstack project with that UUID access to HIL.

Note that the plugin recognizes any user with an `admin` role on any
project as a HIL administrator, similar to the default policy for core
Openstack projects. This is true even for projects not that do not exist
within HIL; such projects will not be able to own resources (such as
nodes networks, etc), but may perform admin-only operations (such as
creating projects).

The HIL command line interface will look for the same `OS_*`
environment variables used by the Openstack command line tools; these
may be set by a user to authenticate when using the CLI.

A script to set these variables correctly can be downloaded from the
Openstack web dashboard via "Access & Security."

## Configuration

As with any other extension, you must load the extension in `hil.cfg`:

    [extensions]
    hil.ext.auth.keystone =

The backend must then be configured to talk to your Keystone server.
The Keystone project maintains documentation on how to do this at:

<http://docs.openstack.org/developer/keystonemiddleware/middlewarearchitecture.html>

Configuring HIL to talk to Keystone deviates in the following ways:

* The paste configuration is not used; you can simply ignore the
  sections that refer to paste.
* The options that the Keystone documentation puts in the section
  `[keystone_authtoken]` should instead be placed in the extension's
  section in `hil.cfg`, i.e. `[hil.ext.auth.keystone]`.

[1]: http://docs.openstack.org/developer/keystonemiddleware/

## Debugging Tips

If authentication is not working with HIL, first check if authentication to OpenStack is working.  Using the OpenStack CLI, run the command:
``openstack token issue -f value -c id``.
If a text token is returned, then authentication to OpenStack is working.

Testing authentication directly to the HIL API is also helpful.
Using the token from the tip above, run:
``curl -H 'x-auth-token: <token>' <HIL address>/nodes/free``.
If the response lists the nodes in the current HIL setup, then the Keystone middleware has been setup correctly.
