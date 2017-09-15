
# Expose network driver capabilites
-----------

[Issue 410](https://github.com/CCI-MOC/hil/issues/410)

We want to expose switch driver capabilities. Capabilities include:

- Jumbo frames are per-switch on our Dell switches and per-port on our Ciscos (#755)
-  QoS (#384)
- Disabling STP (#779)
- DHCP/ARP Snooping (#471)
- Enabling the tagging of DHCP packets with the port number (from @okrieg or @pjd-nu)

# Solution
-----------

* Every switch driver will have a list called `capabilities` in the class. So it would look like
`capabilities = ["require-native-network", "per-port-jumbo-frames"]`

* and then there'll be a method  `get_capabilities()` that returns a boolean if a capability exists or not by checking it in the list.

* an API that needs to test this, can call that method `switch.get_capabilities('require-native-network`) to ensure that the switch supports that method, and then proceed with the original request or error out.

* `show_node()` can be updated to show the capabilities they support.

# Alternative Solutions
-----------------------

@henn proposed that we store the capabilites in a database and those will be mapped
to switch objects. That way we can control indiviual switches instead of a whole
class of switches.

Rest of the steps would remain the same.

# Arch Impact
-----------------

Are there any new architectural assumptions we are now making?
I am making an assumption that we would treat all switches that belong to a class
the same. That is, all brocade switches would have those capabilities as specified
in the Class.

# Security
----------

Doesn't look like it.
```
