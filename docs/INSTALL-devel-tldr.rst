INSTALL-devel-tldr
===================

Following is the simplest way to get started with hacking HIL on Centos system.
Assuming that

  -- You have a github account.
  -- You have already forked the HIL repo.
  -- You would be running HIL in a python virtual environment with SQLite DB as backend.


Install Dependencies::

  yum install epel-release bridge-utils  gcc  httpd  ipmitool libvirt \
  libxml2-devel  libxslt-devel  mod_wsgi net-tools python-pip python-psycopg2 \
  python-virtinst python-virtualenv qemu-kvm telnet vconfig virt-install


Clone repo::

  git clone https://github.com/**username**/hil
  cd hil

Setting python virtual environment::

  virtualenv .venv
  source .venv/bin/activate
  pip install -e .[tests]

Configure HIL::

  cp examples/hil.cfg.dev-no-hardware hil.cfg


Initialize database::

  hil-admin db create

Start server::

  hil serve 5000


From a separate terminal window::

  cd ~/hil/
  virtualenv .venv
  source .venv/bin/activate
  pip install -e .


Testing the setup::

  hil list_nodes all

If the above command reports an empty list.
HIL is successfully installed and ready for hacking.


