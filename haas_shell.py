import haas.command_pattern
import haas.control
import haas.model
import getpass
import sys
import haas.cli
class_name={'group':haas.model.Group,
            'vm':haas.model.VM,
            'port':haas.model.Port,
            'nic':haas.model.NIC,
            'vlan':haas.model.Vlan,
            'switch':haas.model.Switch,
            'node':haas.model.Node,
            'user':haas.model.User}


def show_table(cmd):
    parts = haas.command_pattern.show_table.match(cmd)
    table = parts.group(1)
    if table not in class_name:
        print 'no such table'
        print 'available tables are:'
        for key in class_name:
            print key
        return
    haas.control.query_db(class_name[table])


def auth(user_name,password):
    user = haas.control.get_entity_by_cond(haas.model.User,'user_name=="%s"'%(user_name))
    #print user
    if not user:
        return False
    return user.password == password


while True:
    user_name = raw_input('user:')
    password = getpass.getpass("Password: ")
    if auth(user_name,password):
      haas.control.login_user(user_name)
      break
    print 'invalid user/password combination!'

haas.cli.main_loop()
