import haas.control
import haas.model
import haas.cli


user = haas.control.get_entity_by_cond(haas.model.User,'user_name=="%s"'%('admin'))
if user == None:
    haas.control.create_user('admin','admin')
    print 'No admin user, created one by default'

haas.cli.main_loop()
