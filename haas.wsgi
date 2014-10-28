#!/usr/bin/env python
import haas.api
from haas import config, model
config.load('/etc/haas.cfg')
model.init_db()
from moc.rest import wsgi_handler as application
