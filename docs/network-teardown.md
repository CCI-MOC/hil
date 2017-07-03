# Network Teardown

The script `create_dell_vlans` can be used to pre-populate the bridges
and vlan nics needed for the HIL to operate, but right now we don't
have an automated way to delete them. You shouldn't need to do this to
use the HIL, but if for some reason you want to delete the nics related
to a given vlan, you can do:

    brctl delif br-vlan${vlan_number} em3.${vlan_number}
    vconfig rem em3.${vlan_number}
    ifconfig br-vlan${vlan_number} down
    brctl delbr br-vlan${vlan_number}

We're using `em3` as an example; do a `brctl show` to find out what
the right nic actually is.
