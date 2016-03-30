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

When a new migration script needs to be written, the procedure depends
on whether or not the migration script concerns an extension which does
not already have any migration scripts.

### If the extension does not have migration scripts already

First, choose a directory in which to store the migration scripts for the
extension. Storing the migrations as close to the module as possible is
recommended. Add code to your extension to register this directory with
`haas.migrations.paths`, e.g.:

    from haas.migrations import paths:

    paths[__name__] = 'Path to my migrations directory'

Make sure the value will be correct regardless of where the source tree is
located; making it a function of `__file__` is a good idea. Have a look at
existing extensions for examples if need be. `haas.ext.switches.dell` is a
good example.

Also, make sure that the migration scripts will be included in the final
package. This usually just means adding an appropriate entry to `package_data`
in `setup.py`. If the extension is maintained outside of the HaaS core source
tree, make sure you pass `zip_safe=False` to `setup`.

Next, to generate a template migration, execute:

    haas-admin db migrate --head haas@head \
        --branch-label ${name_of_extension_module} \
        -m 'Summary of change'

Alembic will look at the differences between the schema in the database and
the one derived from the HaaS source, and generate its best attempt at a
migration script. The script will be stored in `haas/migrations/versions`.
Copy it to the directory you chose, and change the value of `down_revision` to
`None`.

Sanity check the output; Alembic often does a good job generating scripts, but
it should not be trusted blindly.

Finally, run `haas-admin db upgrade heads` to upgrade the database according
to your new migration.

### If the extension already has migrations, or the script is for HaaS core

To generate a new migration script, execute:

    haas-admin db migrate --head ${branch_name}@head \
        -m 'Summary of change'

Where `${branch_name}` is either the name of the extension's module (if the
script is for an extension) or `haas` (if the script is for HaaS core).

Alembic will generate a migration script in the appropriate directory. Again,
sanity check the output; Alembic's guesses should not be trusted blindly.

[1]: http://www.sqlalchemy.org/
[2]: http://flask-sqlalchemy.pocoo.org/2.1/
[3]: http://flask.pocoo.org/
[4]: https://flask-migrate.readthedocs.org/en/latest/
[5]: http://alembic.readthedocs.org/en/latest/
[6]: http://flask-script.readthedocs.org/en/latest/
[7]: http://alembic.readthedocs.org/en/latest/branches.html
