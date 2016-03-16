from flask_migrate import Migrate, MigrateCommand
from haas.flaskapp import app
from haas.model import db

migrate = Migrate(app, db)
command = MigrateCommand
