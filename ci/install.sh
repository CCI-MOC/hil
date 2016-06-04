#!/usr/bin/env bash

# Create a new virtualenv with the system 2.7 python
# virtualenv -p /usr/bin/python2.7 --system-site-packages env
# source env/bin/activate

# Setup configuration
cp ci/testsuite.cfg.$DB testsuite.cfg
sudo cp ci/haas.cfg.$DB /etc/haas.cfg
sudo chown travis:travis /etc/haas.cfg

# Database Setup
if [ $DB = postgres ]; then
    sudo apt-get install -y python-psycopg2
    psql --version
    psql -c 'CREATE DATABASE haas_tests;' -U postgres
    psql -c 'CREATE DATABASE haas;' -U postgres
elif [ $DB = sqlite ]; then
    # Workaround to create an empty sqlite db file
    sqlite3 /home/travis/haas.db ".databases"
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
