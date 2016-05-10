Following steps will let you install, configure postgreSQL server and create a
`haas` database for development or production version of HaaS on a 
Centos - 7 server



# Part 1: Install PostgreSQL server. Initialize the system. 
Configure PostgreSQL to allow password authentication

## 1. Install the requisite packages on your server.

```
sudo sudo yum install postgresql-server postgresql-contrib -y
```

## 2. Initialize postgresql:

```
sudo postgresql-setup initdb
```

## 3. Replace the term ident from following lines in 
file `/var/lib/pgsql/data/pg_hba.conf` with `md5`

### Before:

```
# "krb5", "ident", "peer", "pam", "ldap", "radius" or "cert".  Note that
host    all             all             127.0.0.1/32            ident
host    all             all             ::1/128                 ident
#host    replication     postgres        127.0.0.1/32            ident
#host    replication     postgres        ::1/128                 ident
```

### After:

```
# "krb5", "ident", "peer", "pam", "ldap", "radius" or "cert".  Note that
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
#host    replication     postgres        127.0.0.1/32            ident
#host    replication     postgres        ::1/128                 ident
```

## 4. Start postgresql service

```
$ sudo systemctl start postgresql
$ sudo systemctl enable postgresql
```


# Part 2: Setup system user and database role for HaaS. 
Create database `haas` owned by user `haas`

## 1. Create a system user haas:

```
useradd haas -d /var/lib/test1 -m -r
```

## 2. Create a database role named `haas` with priviledges to:
 `-r` create roles; 
 `-d` create databases and 
 `-P` will prompt for the password of the new user. 
This is necessary since we have configured postgreSQL to use password authentication.

```
sudo -i -u postgres

-bash-4.2$ createuser -s -r -d -P haas
Enter password for new role:  <Input password for database role haas>
Enter it again: <Retype password for role haas>
```

Confirm that the role with requisite privileges is created.


**as postgres user**

```
-bash-4.2$ psql -c '\dg'
                             List of roles
 Role name |                   Attributes                   | Member of 
-----------+------------------------------------------------+-----------
 haas      | Create role, Create DB                         | {}
 postgres  | Superuser, Create role, Create DB, Replication | {}
```

for some reason if you wish to delete the user. do the following **as postgres user**:

```
dropuser haas
```
@@Note@@: Make sure that the database role you create corresponds to an existing system user. 
eg. There has to be a system user `haas` to access database role `haas`.


## 3. Create database haas owned by database role haas:

```
sudo -i -u haas
-bash-4.2$ createdb haas
```

**confirm it created a database named haas that is owned by haas**
```
 psql -c '\l'
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
Continue with installation steps as described in Install.rst or Hacking.rst
