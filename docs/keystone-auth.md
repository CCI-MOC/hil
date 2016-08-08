An authentication backend for Openstack's Keystone is maintained in this
source tree as `haas.ext.auth.keystone`. This document describes its
configuration and usage in detail.

NOTE: The HaaS command line interface only supports the keystone v3 API.
The server supports anything supported by [keystonemiddleware][1].

# Usage

Once HaaS has been configured to work with Keystone, an administrator
must manually add Openstack projects to HaaS before they can access the
HaaS API. The HaaS project names must correspond to the Openstack UUIDs.
For example, an administrator may execute the command:

    haas project_create 00de7c85e594473db7461cdf7367166a

To grant the Openstack project with that UUID access to HaaS.

Note that the plugin recognizes any user with an `admin` role on any
project as a HaaS administrator, similar to the default policy for core
Openstack projects.

The HaaS command line interface will look for the same `OS_*`
environment variables used by the Openstack command line tools; these
may be set by a user to authenticate when using the CLI.

A script to set these variables correctly can be downloaded from the
Openstack web dashboard via "Access & Security."

# Configuration

As with any other extension, you must load the extension in `haas.cfg`:

    [extensions]
    haas.ext.auth.keystone =

The backend must then be configured to talk to your keystone server.
The keystone project maintains documentation on how to do this at:

<http://docs.openstack.org/developer/keystonemiddleware/middlewarearchitecture.html>

Configuring HaaS to talk to Keystone deviates in the following ways:

* The paste configuration is not used; you can simply ignore the
  sections that refer to paste.
* The options that the Keystone documentation puts in the section
  `[keystone_authtoken]` should instead be placed in the extension's
  section in `haas.cfg`, i.e. `[haas.ext.auth.keystone]`.

[1]: http://docs.openstack.org/developer/keystonemiddleware/
