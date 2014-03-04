#! /usr/bin/python
import os

def set_access_vlan(port, vlan_id):
    """sets the given port number to access mode, with the given vlan_id."""
    # TODO: we aren't really doing much in the way of error checking here.
    def _backout(f):
        """Back out to the top level prompt."""
        for _ in range(3):
            # On the dell, extra exit commands are ignored. we never delve more
            # than three prompts in, so this should be enough.
            f.write("exit\n")

    with open('/dev/ttyS0', 'w') as f:
        _backout(f)

        # find our way to the prompt for this port:
        f.write("enable\n")
        f.write("config\n")
        f.write("int gi1/0/%d\n" % port)

        # set the vlan
        f.write("sw access vlan %d\n" % vlan_id)

        # set the port to access mode
        f.write("sw mode access\n")
 
        # Just for good measure:
        _backout(f)
