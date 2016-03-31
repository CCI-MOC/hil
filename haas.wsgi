#!/usr/bin/env python
import haas.api
from haas import config, model, server
config.setup('/etc/haas.cfg')
server.init()
from haas.rest import app as application
