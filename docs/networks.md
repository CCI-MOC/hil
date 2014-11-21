# Types of Networks in the HaaS


Networks in the HaaS have three fields:

- 'creator' represents what project created it; or 'admin' if it was
  administrator-created.  If there are still networks created by a project,
  then that project cannot be deleted.  Only the creator has the ability to
  delete a network.

- 'access' represents which project's nodes can access it, or '' (the
  empty string) if all   projects' nodes can.  This will eventually be extended
  into a ACL-style approach.

- 'allocated' represents whether the underlying network ID was taken from the
  network driver's allocation pool.  (The other option is that it was manually
  specified by an administrator.)  This is important for network deletion.

  The command line tool's `network_create` treats an empty string to
  mean that the network should be allocated; any other argument is
  treated as a network ID.

These fields are not really independent of each other.  Here are the legal
combinations, with some explanation:

- (admin,   all,     yes): Public network internal to HaaS
- (admin,   all,     no):  Public network that connects outside the HaaS
- (admin,   project, yes): External provisioning network for one project
- (admin,   project, no):  (kind of useless, but legal)
- (project, project, yes): Normal project-created network


Here are the illegal ones:

- (project, [anything], no): Normal users cannot just assert control of external
      VLANs.

- (project, different project, yes): Normal users cannot share networks with
      other users [yet]

- (project, all, yes): In the same vein, user-created public networks are also
      not allowed.
