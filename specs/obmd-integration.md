# Problem

As discussed in [Issue #417: Serial console support is horribly
fragile][417], the current implementation of serial console support is
not very robust, has known resource leaks, and is generally pretty
janky.

We are developing a separate daemon (called obmd) to manage
the OBMs for nodes. An early version is already available at
<https://github.com/zenhack/obmd>. Rationale is discussed in more detail
in the "Alternative Solutions" section below.

This document proposes changes to HIL to integrate with obmd.

# Solution

## Summary

* OBMs will no longer be drivertized, further discussion below.
* `node_register` will be modified to accept obmd connection info:
  * an admin token
  * a base URL for the node, e.g.
    `https://obmd.example.com/node/mynode`.
* The api calls `start_console` and `stop_console` will be removed.
* Two new api calls will be added:
  * `enable_obm`, which will fetch a token for the node's OBM
     from obmd, storing it in the database. If there is already
     a valid token, it will be silently replaced.
  * `disable_obm`, which will invalidate and then delete the token.
    If there is no token, this is a no-op.
* `project_detach_node` will fail if the obm is "enabled" (i.e., we
  have a valid token). This is consistent with how we manage other
  resource dependencies in HIL.
* All obm related calls will fail if the obm is disabled.
* `show_console` will work differently: instead of dumping the contents
  of an existing log, it will simply check for authorization, and if
  successful, redirect the client to a URL provided by obmd, from which
  they may stream the console. For example:
  `https://obmd.example.org/node/mynode/console?token=<obm-token>`
* All other obm related calls will be changed to simply proxy the
  corresponding calls on obmd.

## Un-drivertizing OBMs

The current proposal is not implementable as a simple obm driver, since
it involves new API calls and altered interfaces. Instead of attempting
to adjust the driver model to allow for this, we will simply
un-drivertize OBMs in HIL. All OBMs will be managed by obmd, and future
OBM drivers (e.g. redfish) will be added to obmd instead.

## Handling of failures

1. `disable_obm` will make changes on obmd *before* committing to the database.
2. enable/disable obm operations succeed silently if the changes to obmd have
   already been made.

(1) ensures that if HIL does not successfully commit, it will fail
"safe." OBM operations will fail because the token stored in the
database is invalid, but no access violations will occur.

(2) ensures that an inconsistency between HIL and obmd can be corrected
just by calling enable or disable. Note that this means in the event of
a failure, HIL and obmd *may* become out of sync, but the consequences
of this basically amount to some bad error messages.

If `enable_obm` creates a token and fails to commit, this is not a problem:
per the above, inconsistencies are easily fixable, and it cannot cause
an access violation. While there is valid token, it is lost and not
available to any user.

# Alternative Solutions

Possible variations:

* We could leave the non-console functionality managed directly by HIL.
  This was discussed in the issue and rejected.
  * One problem is that the obm information (hosts, passwords, etc) now
    has to be in too places.
  * Additionally, for this to work we need direct driver support in two
    daemons; moving it all into one place allows us to simplify the way
    OBMs work in HIL (see the discussion about un-drivertizing OBMs in
    HIL).
* We could attempt to shut down the console in `project_detach_node`,
  rather than just failing if it is connected. This would obviate
  `enable_obm` and `disable_obm`.
  * This was explored and turned out to be very tricky to get right; see
    the discussion on issue #417. It is also inconsistent with our
    approach to resource management elsewhere. @okrieg pointed this out
    and suggested the current approach at the weekly HIL meeting on Nov
    21.
* We could attempt to do streaming of the console in HIL itself, rather
  than have a separate daemon.
  * This was tried in PR #483, but abandoned. We encountered a number of
    difficulties:
    * Synchronizing between request handlers was difficult. If we wanted
      to keep HIL able to run in most WSGI environments, it meant we
      couldn't assume the request handlers were running in the same
      process, or even on the same machine for that matter.
    * The solution basically mandates the use of greenlets for any kind
      of scalability, since otherwise you're tying up a whole thread per
      request, and these are long-lived requests. We could have just
      documented that we expect greenlets, but it makes the api server less
      portable.
      * The daemon, being written in Go, can assume that request
        handlers are light-weight.
* We could try to proxy the console, rather than redirecting, but this
  raises all of same the problems with doing streaming in HIL directly.
* We could try to keep OBMs drivertized within HIL. The trade-offs have
  been discussed above. It's not clear there are significant benefits.
* Instead of passing both obmd's full url to the node and the admin
  token to `node_register`, we could just pass the node label, and add
  `base_url` and `admin_token` options to `hil.cfg`. However, this
  restricts us to only one obmd server, while specifying the URL and
  token per node allows different nodes to be managed by different obmd
  instances.
* Instead of passing both obmd's full url to the node and admin token to
  `node_register`, we could have a separate call `obmd_register`, taking
  the base URL for an obmd server and an admin token. Then,
  `node_register` would take a node label and a label for an obmd
  server. This allows us to de-duplicate the obmd config information,
  while still allowing for multiple obmd servers. It is analogous to
  what we do with switches, which is an advantage. It does mean that HIL
  now knows about which obmd servers exist, whereas with the current
  scheme HIL is entirely agnostic to this, so coupling is a bit looser.
  It's not clear that there is a pragmatic disadvantage, however.

# Arch Impact

Lots, discussed in detail elsewhere in this document.

# Security

* HIL itself no longer needs to have either the credentials for, or
  network connectivity to the OBMs. This is nice.
* Because HIL redirects the user to obmd, both obmd and the HIL api server
  must be network accessible to users.
* Careful attention must be paid in the design to avoid illicit access
  to the OBMs. See discussion above.

[417]: https://github.com/CCI-MOC/hil/issues/417
