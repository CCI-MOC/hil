#!/usr/bin/env python
import haas.api
from haas import config, model, server, migrations
config.setup('/etc/haas.cfg')
server.init()
migrations.check_db_schema()
from haas.rest import app as application
