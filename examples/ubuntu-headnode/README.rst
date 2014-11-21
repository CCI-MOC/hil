This directory contains an example script for generating a base headnode image
for HaaS. The resulting image is identical to the Ubuntu 14.04 cloud image, with
one exception: there is a known root password. The standard cloud image needs
credentials to be provided via cloud-init, which is not necessarily available
in a HaaS environment.

Running ``sudo make`` in this directory will download the cloud image, prompt
you for a password, and make a modified version (same filename with a ``.raw``
at the end) with the root password you supply.

The image will still run cloud-init, but when it boots (which may take some
time) you will be able to log in as mocuser with the chosen password.
