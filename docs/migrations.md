This document describes how to work with HaaS's database migration
framework. It is aimed at developers; for instructions on upgrading a
production database see UPGRADING.rst.

# Introduction

HaaS uses [SQLAlchemy][1] as a database abstraction layer,
[Flask-SQLAlchemy][2] for integration with [Flask][3], and
[Flask-Migrate][4]/[Alembic][5] for migration support. This document
explains HaaS-specific details; refer to the libraries' documentation
for general information about these tools. This document mainly focuses
on Alembic and Flask-Migrate.

HaaS uses migration scripts for updating the database to work
with a new version of the software. Any time the database schema
changes, a migration script must be written so that existing
installations may be upgraded to the next HaaS release automatically.

## Background

Developers unfamiliar with alembic should at least skim the [Alembic
tutorial](http://alembic.readthedocs.org/en/latest/tutorial.html), which
explains general alembic concepts. Developers should also read [the
overview documentation for Flask-Migrate][4], which integrates Alembic
with Flask.

## Usage In HaaS

HaaS uses the migration libraries as follows:

The [Flask-Script][6] extension is used to expose Flask-Migrate's
functionality, via the `haas-admin db` subcommand, implemented in
`haas/commands/`. This command is almost exactly as described in the
[Flask-Migrate][4] documentation, except we've added sub-command `haas
db create`, which initially creates and populates the database tables.
This command is idempotent, so it is safe to run it on an
already-initialized database. When adding extensions to haas.cfg, the
`create` command should be re-run to create any new tables; see
UPGRADING for details.

We use Alembic's [branch support][7] to handle tables created by
extensions; Developers should be familiar with this part of alembic's
interface. Each extension should have its own head. We do not merge
these heads.

When a new migration script needs to be written, a developer may execute
`haas-admin db migrate`, which will generate a script under
`haas/migrations/versions/`. If the migration is for a change in HaaS
core, this is the correct location. If the change is due to an
extension, the script should be moved somewhere closer to the source
code for the extension itself. Note that this works just as well for
third-party extensions maintained outside of the HaaS source tree. Take
care to set the `down_revision` and `branch_labels` fields correctly.
The latter should be a one-element tuple containing the module name for
the extension.

Note that alembic's auto-generation support should not be relied upon to
produce correct scripts; while in many cases it just does the right
thing, you should always verify the output and change as needed.

Extensions using the migration framework must register themselves in the
dictionary `haas.migrations.paths`; see the comments next to its
definition in `haas/migrations.py` for details, and existing extensions
which use it for examples (e.g. `haas.ext.switches.dell`).

[1]: http://www.sqlalchemy.org/
[2]: http://flask-sqlalchemy.pocoo.org/2.1/
[3]: http://flask.pocoo.org/
[4]: https://flask-migrate.readthedocs.org/en/latest/
[5]: http://alembic.readthedocs.org/en/latest/
[6]: http://flask-script.readthedocs.org/en/latest/
[7]: http://alembic.readthedocs.org/en/latest/branches.html
