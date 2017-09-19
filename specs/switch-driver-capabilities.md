
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

* Every switch driver will have a list called `capabilities` in the class. So it would look like
`capabilities = ["require-native-network", "per-port-jumbo-frames"]`

* A new column (text) will be added to the switch table. This will store list of
capabilities encoded as JSON. This could probably default to all capabilities as
specified in the Class.

* A method called `get_capabilities()` would return all capabilities for a switch

* and then there'll be a method  `have_capability()` that returns a boolean if a capability exists or not by checking it in the list.

* an API that needs to test this, can call that method `switch.get_capabilities('require-native-network`) to ensure that the switch supports that method, and then proceed with the original request or error out.

* `show_switch()` will be updated to show switch capabilities.

* `show_node()` can be updated to show the capabilities supported by a nic. This
will be useful for end users to pick nodes based on capabilities.

*

# Alternative Solutions
-----------------------


# Arch Impact
-----------------

None

# Security
----------

Doesn't look like it.
```
