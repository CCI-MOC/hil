This document describes how to work with HIL's database migration
framework. It is aimed at developers; for instructions on upgrading a
production database see UPGRADING.rst.

# Introduction

HIL uses [SQLAlchemy][1] as a database abstraction layer,
[Flask-SQLAlchemy][2] for integration with [Flask][3], and
[Flask-Migrate][4]/[Alembic][5] for migration support. This document
explains HIL-specific details; refer to the libraries' documentation
for general information about these tools. This document mainly focuses
on Alembic and Flask-Migrate.

HIL uses migration scripts for updating the database to work
with a new version of the software. Any time the database schema
changes, a migration script must be written so that existing
installations may be upgraded to the next HIL release automatically.

## Background

Developers unfamiliar with alembic should at least skim the [Alembic
tutorial](http://alembic.readthedocs.org/en/latest/tutorial.html), which
explains general alembic concepts. Developers should also read [the
overview documentation for Flask-Migrate][4], which integrates Alembic
with Flask.

## Usage In HIL

HIL uses the migration libraries as follows:

The [Flask-Script][6] extension is used to expose Flask-Migrate's
functionality, via the `hil-admin db` subcommand, implemented in
`hil/commands/`. This command is almost exactly as described in the
[Flask-Migrate][4] documentation, except we've added sub-command `hil
db create`, which initially creates and populates the database tables.
This command is idempotent, so it is safe to run it on an
already-initialized database. When adding extensions to hil.cfg, the
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
`hil.migrations.paths`, e.g.:

    from hil.migrations import paths:

    paths[__name__] = 'Path to my migrations directory'

Make sure the value will be correct regardless of where the source tree is
located; making it a function of `__file__` is a good idea. Have a look at
existing extensions for examples if need be. `hil.ext.switches.dell` is a
good example.

Also, make sure that the migration scripts will be included in the final
package. This usually just means adding an appropriate entry to `package_data`
in `setup.py`. If the extension is maintained outside of the HIL core source
tree, make sure you pass `zip_safe=False` to `setup`.

Next, to generate a template migration, execute:

    hil-admin db migrate --head hil@head \
        --branch-label ${name_of_extension_module} \
        -m '<Summary of change>'

Alembic will look at the differences between the schema in the database and
the one derived from the HIL source, and generate its best attempt at a
migration script. The script will be stored in `hil/migrations/versions`.
Move it to the directory you chose, and change the value of `down_revision` to
`None`.

Sanity check the output; Alembic often does a good job generating scripts, but
it should not be trusted blindly.

Finally, run `hil-admin db upgrade heads` to upgrade the database according
to your new migration.

### If the extension already has migrations, or the script is for HIL core

To generate a new migration script, execute:

    hil-admin db migrate --head ${branch_name}@head \
        -m '<Summary of change>'

Where `${branch_name}` is either the name of the extension's module (if the
script is for an extension) or `hil` (if the script is for HIL core).

Alembic will look at the differences between the schema in the database and
the one derived from the HIL source, and generate its best attempt at a
migration script. The script will be stored in `hil/migrations/versions`.

The value of `down_revision` should be the identifier of the previous migration script.
The value of `branch_labels` should be `('<branch_name>',)` where `branch_name`
should match what was used in the command to generate the migration script.
Finally, the value of `branch_lables` in the previous migration script
(named by `down_revision` in the new one) must be set to `None`. This
will need to be changed manually.

Sanity check the output; Alembic often does a good job generating scripts, but
it should not be trusted blindly.

## Notes on Generating Migrations and Checking the Output

### State of the Database

For automatic migrations the database being loaded to generate the migration should
match the schema of the current master branch.
To ensure this, create a new PostgreSQL database and initialise it using
`hil-admin db create` while on a branch that is up to date with current HIL
master branch. The command to generate the migration script should then be run
after checking out the branch that has the changes that the script should be generated for.

### Renaming Columns

Alembic will not rename a column, instead it will delete the original column
and create a new one with the new name. This is an issue as the data will then
not be contained in the new column (see Data Migration vs Schema Migration below).
To change the name of a column the script should be edited manually to remove the
lines dropping the old column and creating one with the new name and replace them
with a line altering the column: `op.alter_column(u'<table_name>', '<old_column_name>', new_column_name='<new_column_name>')`

### [Data Migration][8] vs. Schema Migration

The migrations Alembic generates are schema migrations: they will create/delete tables,
columns, and relationships, but they do not populate these with data. This can be an issue,
particularly in the case of a new relationship that would apply to existing data. None of
the existing data will be accessible via the new relationship unless the data itself is
specifically migrated as well.

This can be done by directly encoding data within the script and using a command like
`bulk_insert()`, executing a SQL statement to SELECT the data and INSERT it into the new
column, or by creating a live interaction with the database.

lines 28-32 in ``hil/migrations/versions/89630e3872ec_network_acl.py`` show an example
of executing a SQL statement then using `bulk_insert()` to migrate data.

## Writing tests

The file ``tests/unit/migrations.py`` provides some basic infrastructure
for testing migrations. The comments there describe things in full
detail, but the basic strategy is, back up a database with a known set
of objects using ``pg_dump``, and place the result in
``tests/unit/migrations/``. To generate a dump, execute::

    pg_dump -U $hil_user $database_name --column-inserts > filename.sql

``--column-inserts`` is necessary to ensure that the result can be
loaded via SQLAlchemy; the default is not valid SQL and takes advantage
of specific features of the ``psql`` command. You will also need to edit
the file manually, doing the following:

- It is likely that the system you're developing on will have a newer
  version of postgres than what travis uses, so you may need to remove
  statements setting options that don't exist int he older versions.
  Delete any statements of the form ``SET option_name =  ...``, where
  `option_name` is any of:
  - idle_in_transaction_session_timeout
  - lock_timeout
  - row_security
- Delete all statements using the keywords GRANT, REVOKE, or EXTENSION.
  These will cause permission errors if your database user is not root.
- Delete all statements of the form ``ALTER TABLE ... OWNER TO
  ...``; these may cause failures if the connection details on the
  machine which runs the tests are different from yours, since the
  refer to specific database users/roles.
- At the top of the file, document the following:
  - In roughly what stage of HIL's development this dump was taken,
    e.g. "Just after re-integrating flask" or "first integration of
    openvpn"
  - The git commit hash of the revision of HIL which created the
    database.
  - A list of extensions that were loaded into HIL when the database
    was created.
  - Any other options in the config file that would have affected the
    contents of the database.
  - How the database was generated, e.g. "by the function hil.foo.bar
    as of commit ``$hash``."

[1]: http://www.sqlalchemy.org/
[2]: http://flask-sqlalchemy.pocoo.org/2.1/
[3]: http://flask.pocoo.org/
[4]: https://flask-migrate.readthedocs.org/en/latest/
[5]: http://alembic.readthedocs.org/en/latest/
[6]: http://flask-script.readthedocs.org/en/latest/
[7]: http://alembic.readthedocs.org/en/latest/branches.html
[8]: https://groups.google.com/forum/#!topic/sqlalchemy-alembic/gCJO4W0GKB4
