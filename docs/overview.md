# HaaS Architecture Overview

The HaaS (Hardware as a Service) is a tool used to perform network isolation of physical machines, so that different parties can be given physical capacity within the same data center, without needing to trust each other.

## Operation

From a user's perspective, the HaaS allows one to:

* allocate physical nodes
* create login/management nodes (sometimes called headnodes)
* configure networks, in particular:
  * create logical networks
  * connect physical nodes to those logical networks (on a per-nic basis)
  * connect login/management nodes to those networks.

Once everything is configured as desired, the user "deploys" the configuration, at which point the necessary adjustments will be made to the switch (see below), and the login node will boot.

Right now, we're using 802.1q VLANs to achieve network isolation. The HaaS communicates with a managed switch, to which the physical  hardware is attached. When a "deploy" operation is performed, the HaaS sends commands to the switch which configure the relevant ports as needed to create the logical networks.
