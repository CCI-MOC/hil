#!/usr/bin/env bash

# Setup configuration
cp ci/testsuite.cfg.$DB testsuite.cfg
sudo cp ci/haas.cfg.apache.$DB /etc/haas.cfg
sudo chown travis:travis /etc/haas.cfg

# Database Setup
if [ $DB = postgres ]; then
    sudo apt-get install -y python-psycopg2
    psql --version
    psql -c 'CREATE DATABASE haas_tests;' -U postgres
    psql -c 'CREATE DATABASE haas;' -U postgres
fi

# Install HaaS
python setup.py install

# Apache Setup
sudo chown -R travis:travis /var/www
mkdir /var/www/haas

sed -e "s|%VIRTUAL_ENV%|$VIRTUAL_ENV|g" -i ci/wsgi.conf
sudo cp ci/wsgi.conf /etc/apache2/sites-available/haas.conf
cp haas.wsgi /var/www/haas/haas.wsgi

sudo a2dissite 000-default && sudo a2ensite haas
sudo service apache2 restart
