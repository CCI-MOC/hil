
The following steps will let you install, configure PostgreSQL server and
create a `hil` database for development or production version of HIL on a
Centos - 7 server.

For simplicity of configuration and ease of maintenance we will use
single name `hil` for creating a system user, database role and database name.
This is merely a guideline for users new to database setup and administration.
Experienced users are free to choose any other method that suits their need.
The end goal is to have a way to have a working PostgreSQL backend for `hil`

## Part 1: Install PostgreSQL server.

Initialize the system. Configure PostgreSQL to allow password authentication.

**1. Install the requisite packages on your server.**

```
sudo yum install postgresql-server postgresql-contrib -y
```

**2. Initialize postgresql:**

```
sudo postgresql-setup initdb
```

**3. Replace the term `ident` from following lines**
in file `/var/lib/pgsql/data/pg_hba.conf` with `md5`

**Before:**

```
# "krb5", "ident", "peer", "pam", "ldap", "radius" or "cert".  Note that
host    all             all             127.0.0.1/32            ident
host    all             all             ::1/128                 ident
#host    replication     postgres        127.0.0.1/32            ident
#host    replication     postgres        ::1/128                 ident
```

**After:**

```
# "krb5", "ident", "peer", "pam", "ldap", "radius" or "cert".  Note that
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
#host    replication     postgres        127.0.0.1/32            ident
#host    replication     postgres        ::1/128                 ident
```

**4. Start postgresql service**

```
$ sudo systemctl start postgresql
$ sudo systemctl enable postgresql
```

##Part 2: Setup system user and database role for HIL.

Create database named `hil` owned by user also named as `hil`.

**5. Create a system user hil:**

If you are setting up this database for a [production setup](INSTALL.html)
then you might have already created a system user for managing `HIL`. In that case skip this
step.

If you are setting up database for [development purpose](INSTALL-devel.html)
you will need to create a system user to manage `HIL` database as follows.

**format:** `useradd <username> --system -d <path-to-home-dir> -m -r `

In this case both system username and home directory will be named `hil`

```
useradd hil --system -d /var/lib/hil -m -r
```

**6. Create a database role named `hil` with privileges to:**
 `-r` create roles
 `-d` create databases and
 `-P` will prompt for the password of the new user.
This is necessary since we have configured PostgreSQL to use password authentication.

```
$ sudo -u postgres createuser -r -d -P hil
Enter password for new role:  <Input password for database role hil>
Enter it again: <Retype password for role hil>
```

Confirm that the role with requisite privileges is created **as postgres user**:

```
$ psql -c '\dg'
                             List of roles
 Role name |                   Attributes                   | Member of
-----------+------------------------------------------------+-----------
 hil      | Create role, Create DB                         | {}
 postgres  | Superuser, Create role, Create DB, Replication | {}
```

**Note**: It is recommended that the PostgreSQL role and database you create correspond to an existing system user.
eg. There should be a system user `hil` to access database named `hil` as database role named `hil`.
Advanced user/role/database configurations may not need to follow this rule.  More information is available in the [Database Roles and Privileges](https://www.postgresql.org/docs/9.0/static/user-manag.html) reference guide.


**7. Create database hil owned by database role hil:**

```
sudo -u hil createdb hil
```

confirm it created a database named `hil` and it is owned by `hil`.

```
$ psql -c '\l'
                                  List of databases
   Name    |  Owner   | Encoding |   Collate   |    Ctype    |   Access privileges
-----------+----------+----------+-------------+-------------+-----------------------
 hil      | hil     | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
 postgres  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
 template0 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
           |          |          |             |             | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
           |          |          |             |             | postgres=CTc/postgres
```

##Finally:

If you have followed all steps so far.
Put following string in `hil.cfg` under section `[database]`

```
uri = postgresql://hil:<clear text password >@localhost:5432/hil
```

It follows the format: `postgresql://<user>:<password>@<address>/<dbname>`
where ``<user>`` is the name of the postgres user you created, ``<password>`` is
its password, ``<dbname>`` is the name of the database you created, and
``<address>`` is the address which hil should use to connect to postgres (In a
typical default postgres setup, the right value is ``localhost``).

Continue with installation steps:

[continue with production install](INSTALL.html)
or
[continue with development install](INSTALL-devel.html)
