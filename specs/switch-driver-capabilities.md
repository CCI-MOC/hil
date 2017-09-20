
# Expose network driver capabilites
-----------

[Issue 410](https://github.com/CCI-MOC/hil/issues/410)

We want to expose switch driver capabilities. Capabilities could include:

- Jumbo frames are per-switch on our Dell switches and per-port on our Ciscos (#755)
-  QoS (#384)
- Disabling STP (#779)
- DHCP/ARP Snooping (#471)
- Enabling the tagging of DHCP packets with the port number (from @okrieg or @pjd-nu)

# Solution
-----------

* All switch drivers would have a method called get_capabilities.

* This method would return a list with all capabilities supported by the switch.
It's implementation could be flexible; it could simply return a hardcoded list, or generate it from some database.

* an API that needs to check for capabilities, can call `get_capabilties()` and then
check if it exists in the list or not.

* `show_switch()` will be updated to show switch capabilities.

* `show_node()` can be updated to show the capabilities supported by a nic. This
will be useful for end users to pick nodes based on capabilities. Admins would
see all capabilities while non-admin users would only see certain limited capabilities.
What to show and what not show under this can be decided as we add support for
a new switch capability.


# Alternative Solutions
-----------------------


# Arch Impact
-----------------

None

# Security
----------

Doesn't look like it.
```
