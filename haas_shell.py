import haas.control
import haas.model
import getpass
import sys
import haas.cli

def auth(user_name,password):
    user = haas.control.get_entity_by_cond(haas.model.User,'user_name=="%s"'%(user_name))
    if not user:
        return False
    return user.password == password

user = haas.control.get_entity_by_cond(haas.model.User,'user_name=="%s"'%('admin'))
if user == None:
    haas.control.create_user('admin','admin')
    print 'No admin user, created one by default'


while True:
    user_name = raw_input('user: ')
    password = getpass.getpass("Password: ")
    if auth(user_name,password):
        haas.control.login_user(user_name)
        break
    print 'invalid user/password combination!'

haas.cli.main_loop()
