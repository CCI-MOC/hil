Here is the consistency model for our database.

  - The entire project has a 'dirty bit', which represents if the networking
    information has been applied/deployed.

  - ``project_apply``: Take the networking state as the database sees it, and
    make the world match.  This is idempotent.  This clears the dirty bit.

  - ``node_attach_network``, ``node_detach_network``: These don't affect the
    outside world, so they happen immediately.  These set the dirty bit,
    because the real world and the database now disagree.

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
    you do this, the headnode is /locked/, and no more changes to it are
    allowed.

  - ``headnode_delete``: This deletes the headnode immediately, detaching it from
    all networks it was attached to.

  - ``headnode_power_on``, ``headnode_power_off``: These cycle power on the headnode.
    It's possible that headnode_start and headnode_power_on should be the same
    thing.  It's also possible that, eventually, we might allow networking
    changes to powered-off headnodes.  (It's semantically reasonable, but
    might be tricky in implementation.)
