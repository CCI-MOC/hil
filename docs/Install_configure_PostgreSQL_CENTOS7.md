
The following steps will let you install, configure PostgreSQL server and
create a `haas` database for development or production version of HaaS on a
Centos - 7 server.

For simplicity of configuration and ease of maintenance we will use 
single name `haas` for creating a system user, database role and database name.
This is merely a guideline for users new to database setup and administration.
Experienced users are free to choose any other method that suits their need.
The end goal is to have a way to have a working PostgreSQL backend for `haas`

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

##Part 2: Setup system user and database role for HaaS.

Create database named `haas` owned by user also named as `haas`.

**5. Create a system user haas:**

If you are setting up this database for a [production setup](production/INSTALL.rst)
then you might have already created a system user for managing `HaaS`. In that case skip this 
step.

If you are setting up database for [development purpose](development/HACKING.rst)
you will need to create a system user to manage `HaaS` database as follows.

**format:** `useradd <username> --system -d <path-to-home-dir> -m -r `

In this case both system username and home directory will be named `haas`

```
useradd haas --system -d /var/lib/haas -m -r
```

**6. Create a database role named `haas` with priviledges to:**
 `-r` create roles
 `-d` create databases and 
 `-P` will prompt for the password of the new user. 
This is necessary since we have configured PostgreSQL to use password authentication.

```
$ sudo -u postgres createuser -r -d -P haas
Enter password for new role:  <Input password for database role haas>
Enter it again: <Retype password for role haas>
```

Confirm that the role with requisite privileges is created **as postgres user**:

```
$ psql -c '\dg'
                             List of roles
 Role name |                   Attributes                   | Member of 
-----------+------------------------------------------------+-----------
 haas      | Create role, Create DB                         | {}
 postgres  | Superuser, Create role, Create DB, Replication | {}
```

If you wish to delete the user, do the following:

```
$ sudo -u postgres dropuser haas
```
**Note**: Make sure that the database role you create corresponds to an existing system user. 
eg. There has to be a system user `haas` to access database named `haas` as database role named `haas`.


**7. Create database haas owned by database role haas:**

```
sudo -u haas createdb haas
```

confirm it created a database named `haas` and it is owned by `haas`.

```
$ psql -c '\l'
                                  List of databases
   Name    |  Owner   | Encoding |   Collate   |    Ctype    |   Access privileges   
-----------+----------+----------+-------------+-------------+-----------------------
 haas      | haas     | UTF8     | en_US.UTF-8 | en_US.UTF-8 | 
 postgres  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | 
 template0 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
           |          |          |             |             | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
           |          |          |             |             | postgres=CTc/postgres
```

##Finally:

If you have followed all steps so far. 
Put following string in `haas.cfg` under section `[database]`

```
uri = postgresql://haas:<clear text password >@localhost:5432/haas
```

It follows the format: `postgresql://<user>:<password>@<address>/<dbname>`
where ``<user>`` is the name of the postgres user you created, ``<password>`` is
its password, ``<dbname>`` is the name of the database you created, and
``<address>`` is the address which haas should use to connect to postgres (In a
typical default postgres setup, the right value is ``localhost``).

Continue with installation steps:

[continue with production install](INSTALL.rst)
or 
[continue with development install](INSTALL-devel.rst)
