# Consistency model

Here is the consistency model for headnodes.

  - ``headnode_create``: After running this, you can then run
    ``headnode_create_nic``, ``headnode_delete_nic``,
    ``headnode_connect_network``, ``headnode_detach_network`` as much as you
    want, until you run ``headnode_start``.  The headnode's VM is then
    created, started, and connected to the appropriate networks.  As soon as
    you do this, the headnode becomes 'frozen', and no more changes to it are
    allowed.  (Currently, the headnode is marked dirty/clean instead of
    unfrozen/frozen.  This lines up with the semantics in one way, in that a
    dirty headnode hasn't been fully applied yet.  But, they act different
    enough that this will probably change.  This change will not affect
    external behavior.)

  - ``headnode_delete``: This deletes the headnode immediately, detaching it
    from all networks it was attached to.  Due to current limitations, this
    operation cannot be run at all.  Eventually, this call should succeed as
    long as the headnode is powered off.

  - ``headnode_start``, ``headnode_stop``: These cycle power on the headnode.
    It's also possible that, eventually, we might allow networking changes to
    powered-off headnodes.  (It's semantically reasonable, but might be tricky
    in implementation.)
