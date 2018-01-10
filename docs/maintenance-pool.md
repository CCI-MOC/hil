# Maintenance Pool

## Overview

The maintenance pool is an optional service implemented by server administrators
that ideally performs extra operations on nodes after they have been removed from a project
by `hil project_detach_node`. If enabled, HIL will move the node from its original project
into the designated maintenance project.  Then, HIL will POST to the URL of the service with
the name of the node.

Maintenance service example: Once the POST is received, the maintenance service
logs when the node was detached, wipes the disks, sets the boot device to PXE, and then
frees the node from the maintenance pool with `hil project_detach_node`.

## Configuration

The maintenance pool will be active if the `maintenance` section exists in hil.cfg.
If so, `maintenance_project` must be set equal to the
name of the maintenance project registered in HIL and `url` must point at the maintenance
service.
