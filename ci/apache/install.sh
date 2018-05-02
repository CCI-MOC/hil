#!/usr/bin/env bash

# Exit if we are only running unit tests
if [ $TEST_SUITE = unit ]; then
	exit 0
fi

# Apache Setup
sudo chown -R travis:travis /var/www
mkdir /var/www/hil

sudo cp ci/wsgi.conf /etc/apache2/sites-available/hil.conf
sudo sed -e "s|%VIRTUAL_ENV%|$VIRTUAL_ENV|g" -i /etc/apache2/sites-available/hil.conf
cp hil.wsgi /var/www/hil/hil.wsgi

sudo a2dissite 000-default && sudo a2ensite hil
sudo service apache2 restart
