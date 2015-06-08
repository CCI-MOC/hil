HaaS supports a simple extension mechanism, to allow external plugins
to implement things we don't want in the HaaS core. One obvious example
of this is drivers.

Extensions are python modules. The ``extensions`` section in ``haas.cfg``
specifies a list of modules to import on startup, for example::

    [extensions]
    haas.ext.driver.switch.dell =
    haas.ext.driver.switch.complex_vlan =
    haas.ext.driver.obm.ipmi =
    some_3rd_party.haas.drivers.obm.robotic_power_button_pusher

The module must initialize itself as a side-effect of being imported. Most
modules shouldn't need to do much here; HaaS core should facilitate making
load-time work minimal.

All parts of the HaaS source tree which extensions are allowed to access clearly
document this. Here is a summary (see the docstrings in the specific components
for details):

* most of haas.network_allocator
* Model and AnonModel from haas.model
