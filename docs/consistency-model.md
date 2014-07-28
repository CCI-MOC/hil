Here is the consistency model for our database.

  - The entire project has a 'dirty bit', which represents if the networking
    information has been applied.  Operations that do not mention the dirty
    bit neither check nor set it.

  - ``project_apply``: Take the networking state as the database sees it, and
    make the world match.  If the operation succeeds, this clears the dirty
    bit.  (If it fails, it does not alter the dirty bit.)  It is idempotent,
    so it can be re-run as desired.  Notably, it can be used both to apply
    changes made to a project, as well as to restore networking state that was
    upset by some manual change.

  - ``node_attach_network``, ``node_detach_network``: When these operations
    are run, they immediately change the database.  But, the actual networking
    of the project does not change until ``project_apply`` is run.  So, these
    two operations set the dirty bit, because the real world and the database
    now disagree.

  - ``project_attach_node``, ``network_create``: These don't have any effect
    on the outside world, so they happen immediately.

  - ``project_detach_node``, ``network_delete``: These also don't have any
    effect on the outside world, so they also happen immediately.  However,
    these commands can only be run on node/networks that are completely
    unattached (for security reasons).  Furthermore, these cannot happen if
    the the project is dirty (to ensure that they're unattached in the real
    world, as well as in the database).

  - ``headnode_create``: After running this, you can then run
    ``headnode_create_nic``, ``headnode_delete_nic``,
    ``headnode_attach_network``, ``headnode_detach_network`` as much as you
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
