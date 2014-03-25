from haas import control, model, cli
user = control.get_entity_by_cond(model.User,'user_name=="%s"'%('admin'))
if user == None:
    control.create_user('admin','admin')
    print 'No admin user, created one by default'

cli.main_loop()
