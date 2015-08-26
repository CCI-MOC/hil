#!/usr/bin/env python
import haas.api
from haas import config, model, server
config.load('/etc/haas.cfg')
config.configure_logging()
config.load_extensions()
server.init()
from haas.rest import wsgi_handler as application
