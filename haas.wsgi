#!/usr/bin/env python
import haas.api
from haas import config, model
config.load('/etc/haas.cfg')
config.configure_logging()
config.load_extensions()
model.init_db()
from haas.rest import wsgi_handler as application
