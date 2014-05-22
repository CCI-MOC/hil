The devel branch of the haas provides no good automated way of tearing
down the network state created when deploying a group. Here's how to
do it manually:

    brctl delif br-vlan${vlan_number} em3.${vlan_number}
    vconfig rem em3.${vlan_number}
    ifconfig br-vlan${vlan_number} down
    brctl delbr br-vlan${vlan_number}

We're using `em3` as an example; do a `brctl show` to find out what
the right nic actually is.
