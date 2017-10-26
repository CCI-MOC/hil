#!/usr/bin/env bash
#
# Helper script for setting up and running keystone. Most of this is taken from:
#
#   http://docs.openstack.org/developer/keystone/developing.html

# tunable variables:

# So we can avoid repeatedly downloading the repo when developing this script:
keystone_repo=${keystone_repo:-https://git.openstack.org/openstack/keystone}

# git commit to use. Travis uses this to test against different releases of
# keystone:
keystone_commit=${keystone_commit:-master}

# virtualenv executable; on some systems it may be named something else, e.g.
# if we want to test against python 2 on a system for which python 3 is the
# default, the executable will be virtualenv2:
virtualenv_bin=${virtualenv_bin:-virtualenv}

# -e: Stop on the first failing command.
# -x: Print commands as they are executed.
set -ex

# If we're already in a virtualenv, deactivate it; we want to use one that just
# has keystone dependencies. `|| true` prevents this from failing if we're not
# in a venv.
deactivate || true

# Make sure we're in the directory containing this script; this way the user
# can call it from anywhere.
cd "$(dirname $0)"

case "$1" in
  setup)

    git clone ${keystone_repo} keystone
    cd keystone
    git checkout ${keystone_commit}

    ${virtualenv_bin} .venv
    source .venv/bin/activate

    # On some distros (e.g. Ubuntu 14.04), the installed version of pip is
    # too old to parse some of the syntax used in keystone's requirements.txt.
    # Make sure we have the latest:
    pip install --upgrade pip

    # Use the constraints file to provide an upper bound for package versions.
    pip install \
        -r requirements.txt \
        -c https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=${keystone_commit}
    pip install .
    pip install uwsgi # To actually run keystone; no webserver in the deps.

    cp etc/keystone.conf.sample etc/keystone.conf

    sudo mkdir /etc/keystone
    sudo chown $USER:$USER /etc/keystone

    keystone-manage db_sync
    keystone-manage fernet_setup
    keystone-manage credential_setup

    # Populate the database with some sample data. First, make sure keystone is
    # running:
    ../keystone.sh run &
    pid=$!
    # Doing this after launching keystone will give it plenty of time to get
    # started without adding any wasteful calls to sleep:
    pip install -c https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=${keystone_commit} \
        python-openstackclient

    source ../keystonerc # for $OS_PASSWORD
    ADMIN_PASSWORD=s3cr3t ./tools/sample_data.sh

    # In addition to the sample data from the keystone project's script above,
    # we add an extra project and user for use in the tests:
    openstack project create non-hil-project
    openstack user create \
      non-hil-user \
      --password secret
    openstack role add \
      --project non-hil-project \
      --user non-hil-user \
      service

    # stop the server:
    kill $pid
    wait

    ;;
  run)
    cd keystone
    source .venv/bin/activate
    uwsgi \
      --http 127.0.0.1:35357 \
      --wsgi-file "$(which keystone-wsgi-admin)" \
      --ini ../uwsgi.ini &
    admin_pid=$!
    uwsgi \
      --http 127.0.0.1:5000 \
      --wsgi-file "$(which keystone-wsgi-public)" \
      --ini ../uwsgi.ini &
    public_pid=$!
    # If we're killed, propogate the signal to our children.
    trap "kill $public_pid; kill $admin_pid" INT TERM
    wait $public_pid
    wait $admin_pid
    ;;
  *)
    echo "Usage: $0 (setup|run)" >&2
    exit 1
    ;;
esac
