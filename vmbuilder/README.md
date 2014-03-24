This directory contains scripts for generating a base headnode vm image.

Right now the scripts will only work on ubuntu/debian, as a consequence
of being based on vmbuilder. If using the image on other sysetems (e.g.
CentOS) is desired, the disk image will have to be built on a compatible
system and then copied.

To build the disk image, run:

    sudo make

To install it as a vm named `base-headnode` in the local libvirtd
instance, run:

    sudo make install

From there, headnodes can be created via virt-clone, or the HaaS.
