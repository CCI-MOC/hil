# Types of Networks in the HIL


Networks in the HIL have three fields:

- 'owner' represents what project owns it; or 'admin' if it was
  administrator-created.  If there are still networks owned by a project,
  then that project cannot be deleted.  Only the owner has the ability to
  delete a network.

- 'access' represents which projects' nodes can access it, or `[]` (the
  empty list) if all   projects' nodes can.

- 'allocated' represents whether the underlying network ID was taken from the
  network driver's allocation pool.  (The other option is that it was manually
  specified by an administrator.)  This is important for network deletion.

  The command line tool's `network_create` treats an empty string to
  mean that the network should be allocated; any other argument is
  treated as a network ID.

These fields are not really independent of each other.  Here are the legal
combinations, with some explanation:

- (admin,   all,     yes): Public network internal to HIL
- (admin,   all,     no):  Public network that connects outside the HIL
- (admin,   project, yes): External provisioning network for one project
- (admin,   project, no):  (kind of useless, but legal)
- (project, project, yes): Normal project-created network


Here are the illegal ones:

- (project, [anything], no): Normal users cannot just assert control of external
      VLANs.

- (project, all, yes): In the same vein, user-created public networks are also
      not allowed.

- (project, different project, yes): Projects can grant access to other networks later using 'network_grant_project_access', but must have the project that is the owner of the network on the access list.

