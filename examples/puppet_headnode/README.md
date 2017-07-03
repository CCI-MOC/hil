These puppet manifests set up an ubuntu 14.04 headnode to pxe boot
nodes into the CentOS 6.6 installer, with a kickstart file which will
automate the install.

# Setup

1. Create a headnode. The headnode must have a nic that will be
   recognized as eth1, which must be on a HIL network that the nodes
   will pxe boot off of.
2. Download the CentOS 6.6 minimal ISO, verify the checksum, and then
   copy it to root's home directory:

    ./download_iso.sh
    sha256sum -c sha256sums.txt
    cp *.iso /root

3. Install puppet:

    apt-get install puppet

4. Git clone the hil to /root, cd into the examples/puppet_headnode/.

    cd /root
    git clone https://github.com/CCI-MOC/hil
    cd hil/examples/puppet_headnode

5. You may then wish to modify some of the files therein; in
   particular:

   * `manifests/static/pxelinux_cfg` is the pxelinux config file that
     will be used to boot nodes into the installer. The `ksdevice=...`
     parameter must refer to the nic that will be used to fetch the
     kickstart file, which must be the nic that is on a network with
     the headnode. (typically the boot nic). Adjust this if needed.
   * Similarly, the kickstart file `manifests/static/ks.cfg` contains
     information on setting up the network, including during the
     install. This should be modified to match your system. See the
     comments in that file for more detail.
   * **very** importantly, change the default root password in the
     ks.cfg. It's important to do this *before* performing the install.

6. Finally, apply the manifests:

    puppet apply manifests/site.pp

   Note that the hil repo *must* be located under /root; the puppet
   manifests hard-code paths to certain files.

7. Reboot the headnode.

# Use

The manifests install a script `make-links`, which expects a list of mac
addresses to be supplied on its standard input, one per line, e.g:

    01:23:45:67:89:ab
    cd:ef:01:23:45:67
    ...

Each of these should be the mac address off of which you expect a node
to boot. `make-links` will then make some symlinks, the effect of which
is that the corresponding nodes will boot into the CentOS installer on
their next boot (by default, they will chainload to the disk). You can
then use the HIL API to force-reboot the nodes.

Upon completion of the install, the corresponding links will be deleted,
and the node will boot into the new OS for the first time.
