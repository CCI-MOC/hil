Extensions
==========

HIL supports a simple extension mechanism, to allow external plugins
to implement things we don't want in the HIL core. One obvious example
of this is drivers.

Extensions are python modules. The ``extensions`` section in ``hil.cfg``
specifies a list of modules to import on startup, for example::

    [extensions]
    hil.ext.driver.switch.dell =
    hil.ext.driver.switch.complex_vlan =
    hil.ext.driver.obm.ipmi =
    some_3rd_party.hil.drivers.obm.robotic_power_button_pusher

If the extension requires any kind of initialization, it may define a function
``setup``, which will be executed after all extensions have been loaded.
This function must accept arbitrary arguments (for forwards compatibility),
but at present must not rely on the presence or value of any argument.

If the extension needs its own configuration options, it may read them from a
section with the same name as the module, e.g.:

    [extensions]
    some_3rd_party.hil.drivers.obm.robotic_power_button_pusher

    [some_3rd_party.hil.drivers.obm.robotic_power_button_pusher]
    push_duration = 3 seconds

Extensions should not make use any part of the HIL source tree that does not
explicitly invite it (i.e. everything by default is *Private*). Components
which may be used from extensions will explicitly say so in their
documentation, (and describe in detail how they may be used).
Extension-approved components currently include:

* Most of hil.network_allocator
* hil.auth
* From hil.model:
    * db.Model
    * Switch
* The migration framework; see `Migrations <migrations.html>`_ for an overview.

See the docstrings for each component for details.

Additionally, extensions may add wsgi middleware to the flask
application from their ``setup`` function. For example:

    app.wsgi_app = my_middleware(app.wsgi_app)

Note that the order in which the ``setup`` functions are run is not
defined. As such, if multiple extensions add wsgi middleware the
order in which they are applied is also undefined. Using more than one
such extension is discouraged. An ordering *may* be defined in the
future.
