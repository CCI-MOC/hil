We will implement a new microservice to manage vpns, which will consist
of two separate programs:

* `hil-vpnd`, which is a daemon exposing a rest api for manipulating
  vpns
* `hil-vpn-privop`, a wrapper for the priviledged operations needed by
   the daemon.

HIL will talk to the daemon to manage vpns

# Privileged operation wrapper

`hil-vpn-privop` is a command line tool providing a narrow interface:

* `hil-vpn-privop create <name> <vlan-no> <port-no>` creates an openvpn
  configuration under the name `<name>`, which attaches to `<vlan-no>`
  and listens on `<port-no>`. It generates a static key and prints it
  to stdout.
* `hil-vpn-privo start <name>` starts an openvpn process for the config
  `<name>`.
* `hil-vpn-privop stop <name>` stops the openvpn process for the config
  `<name>`.
* `hil-vpn-privop delete <name>` deletes the config for `<name>`. The
  vpn must be stopped for this to work.
* `hil-vpn-privop list` lists the available configs.

To allow the daemon to invoke this tool, an administrator will add an
entry to `/etc/sudoers` like:

```
hil-vpnd ALL = (root) /usr/libexec/hil-vpn-privop
```

where `hil-vpnd` is the user which the daemon will run as. For extra
security, we will recommend setting the permissions on the file to deny
execution to other users entirely.

# The daemon

## Authentication

The daemon will be called by HIL, and will provide a very simple
authentication scheme (probably the same as the AdminToken used by
obmd). It will not need to be accessible by users, though the openvpn
process do for obvious reasons.

## API

The daemon provides a REST API for manipulating vpns attached to VLANs.
it uses `hil-vpn-privop` to perform privileged operations, in order to
minimize attack surface.

### Create a new vpn

`POST /vpns/new`

Request body

```
{
    "vlan": 3231,
}
```

Response body:

```json
{
    "key": "<pem-encoded key>",
    "id": "<unique-id>",
    "port": 9321
}
```

Allocates a new vpn attached to the specified vlan. Returns the port
number on which it is listening, along with a unique identifier and
a pem encoded key.

### Delete a vpn

`DELETE /vpns/<id>`

where `<id>` is the id from the body of the call that created vpn.

# Openvpn details

We will use openvpn with a shared static key, roughly as described here:

<https://openvpn.net/index.php/open-source/documentation/miscellaneous/78-static-key-mini-howto.html>

(Though we will use tap devices, rather than tun, so we're operating at
layer 2 instead of 3).

The microservice will generate the keys, to reduce attack service --
this way we don't have to assume the pem parsers associated with openvpn
are secure.

We will use basically the same logic for connecting tap devices to vlans
as we currently use with headnodes in HIL. This involves a pre-allocated
pool of interfaces (in HIL we create this with the `create_interfaces`
script). We can probably re-use much of the code.  We'll also need to
specify a range of ports to use for the vpns.

Creating a vpn will consist of generating a key and configuration file
in an appropriate location, which will refer to the key and specify a
tap device corresponding to the appropriate vlan. We can manage the
life cycle of the openvpn processes via systemd.
