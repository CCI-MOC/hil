This directory contains example scripts for generating a base headnode image
for HIL. The resulting image is identical to either the Ubuntu 14.04 cloud
image, or the one for CentOS 7, with one exception: there is a known root
password. The standard cloud image needs credentials to be provided via
cloud-init, which is not necessarily available in a HIL environment.

Running ``sudo make distro=$DISTRO`` (where $DISTRO is either ``ubuntu`` or
``centos``) in this directory will download the cloud image, prompt
you for a password, and make a modified version (same filename with a ``.raw``
at the end) with the root password you supply.

The image will still run cloud-init, but when it boots (which may take some
time) you will be able to log in as root with the chosen password.

This can easily be extended to use other distros' cloud images; copy one of the
.mk files, adjust the values of MIRROR and IMG_IN, and creata a
SHA256SUMS.distro for your distro.
