#!/usr/bin/env bash

# Setup configuration
cp ci/testsuite.cfg.$DB testsuite.cfg
sudo cp ci/apache/hil.cfg.$DB /etc/hil.cfg
sudo chown travis:travis /etc/hil.cfg

# Database Setup
if [ $DB = postgres ]; then
    sudo apt-get install -y python-psycopg2
    psql --version
    psql -c 'CREATE DATABASE hil_tests;' -U postgres
    psql -c 'CREATE DATABASE hil;' -U postgres
fi

# Install HIL
python setup.py install

# Apache Setup
sudo chown -R travis:travis /var/www
mkdir /var/www/hil

sed -e "s|%VIRTUAL_ENV%|$VIRTUAL_ENV|g" -i ci/wsgi.conf
sudo cp ci/wsgi.conf /etc/apache2/sites-available/hil.conf
cp hil.wsgi /var/www/hil/hil.wsgi

sudo a2dissite 000-default && sudo a2ensite hil
sudo service apache2 restart
