#!/usr/bin/env python

# imported for the side-effect of registering the request handlers:
from haas import api  # pylint: disable=unused-import

from haas import config, server, migrations

config.setup('/etc/haas.cfg')
server.init()
migrations.check_db_schema()

# we're importing this just to expose the variable, making this a valid
# wsgi script. The "noqa" prevents a pep8 error about not being at the
# top of the file.
#
# pylint: disable=unused-import
from haas.rest import app as application  # noqa
