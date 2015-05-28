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

Documentation on what parts of the HaaS codebase extensions are allowed to use
will be forthcoming; for now the answer is "none," which is not terribly useful.

The module must initialize itself as a side-effect of being imported. Most
modules shouldn't need to do much here; The plan is for drivers (as an example),
defining subclasses of the appropriate types will be enough for them to be
picked up automatically.
