#!/usr/bin/env bash
set -ex

# Skip if we are in the sqlite build
if [ $DB = sqlite ]; then
    exit 0
fi

# these changes optimize postgres. They are fine for testing, but not suitable
# for production.
# See https://www.postgresql.org/docs/current/static/non-durability.html
echo "fsync = off
synchronous_commit = off
full_page_writes = off
checkpoint_timeout = 30min
"| sudo tee --append /etc/postgresql/9.*/main/postgresql.conf

sudo service postgresql restart
