#!/bin/bash

# There has to be a better way to set permissions on the stuff in copy-files.

chown root:root $1/usr/local/bin/power_cycle
chmod 755 $1/usr/local/bin/power_cycle

chown root:root $1/etc/network/interfaces
chmod 644 $1/etc/network/interfaces
