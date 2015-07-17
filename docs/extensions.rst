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

If the extension requires any kind of initialization, it may define a function
``setup``, which will be executed after all extensions have been loaded.
This function must accept arbitrary arguments (for forwards compatibility),
but at present must not rely on the presence or value of any argument.

If the extension needs it's own configuration options, it may read them from a
section with the same name as the module, e.g.:

    [extensions]
    some_3rd_party.haas.drivers.obm.robotic_power_button_pusher

    [some_3rd_party.haas.drivers.obm.robotic_power_button_pusher]
    push_duration = 3 seconds

All parts of the HaaS source tree which extensions are allowed to access clearly
document this. Here is a summary (see the docstrings in the specific components
for details):

* most of haas.network_allocator
* From haas.model:
  * AnonModel
  * Model
  * Switch
