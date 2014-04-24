from model import *
from haas.config import cfg, register_callback
import haas.headnode
import os
import os.path
import sys
import tabulate
current_user = ""
class_name={'group':Group,
            'vm':VM,
            'port':Port,
            'nic':NIC,
            'vlan':Vlan,
            'switch':Switch,
            'node':Node,
            'user':User}

@register_callback
def validate_config():
    """ Returns True if the config file has valid data, False (w/ the error
        string) otherwise.

        This  implementation checks for the presence of an active_switch
        option in the general section of the config file. It then loads the
        required driver module, and calls the driver's config validator
        function.
    """
    if not(cfg.has_section('general')):
        return (False, "[Control]: Missing mandatory \"general\" section.")
    if not(cfg.has_option('general', 'active_switch')):
        return (False, "[Control]: Missing mandatory \"active_switch\" option.")

    active_switch_str = cfg.get('general', 'active_switch')
    active_switch = __import__("haas.drivers." + active_switch_str, fromlist = ["*"])

    return active_switch.validate_config()

def show_table(table_name):
    if table_name not in class_name:
        print 'no such table'
        print 'available tables are:'
        for key in class_name:
            print key
        return
    query_db(class_name[table_name])
                
                                                                        


from sqlalchemy.exc import IntegrityError, InvalidRequestError

class DuplicateError(Exception):
    pass

class NotExistError(Exception):
    pass

class NotAvailableError(Exception):
    pass

def query_db(classname):
    all=session.query(classname).all()
    table = [classname.meta]
    for some in all:
        table.append(some.list_repr())
    print tabulate.tabulate(table,headers="firstrow")
    print
    return all

def create_user(user_name,password):
    user = User(user_name,password)
    session.add(user)
    session.commit()

def login_user(user_name):
    global current_user
    current_user = user_name

def check_available(classname,cond):
    """
    classname specifies which kind of objects
    cond is a string like "node_id==2"
    """
    return session.query(classname).filter(cond).first().available

def get_entity_by_cond(classname,cond):
    return session.query(classname).filter(cond).first()

def create_node(node_id):
    node = Node(node_id)
    session.add(node)
    session.commit()

def create_nic(nic_id,mac_addr,name):
    nic = NIC(nic_id,mac_addr,name)
    session.add(nic)
    session.commit()

def add_nic(nic_id,node_id):
    nic = get_entity_by_cond(NIC,'nic_id==%d'%nic_id)
    node = get_entity_by_cond(Node,'node_id==%d'%node_id)
    for node_nic in node.nics:
        if node_nic.name == nic.name:
            raise DuplicateError("NIC name duplicate")
    nic.node = node
    session.commit()

def create_switch(switch_id,script):
    switch = Switch(switch_id, script)
    session.add(switch)
    session.commit()
def create_port(port_id,switch_id,port_no):
    switch = get_entity_by_cond(Switch,'switch_id==%d'%switch_id)
    port = Port(port_id,port_no)
    port.switch = switch
    session.add(port)
    session.commit()
def connect_nic(nic_id, port_id):
    nic  = get_entity_by_cond(NIC,'nic_id==%d'%nic_id)
    port = get_entity_by_cond(Port, 'port_id==%d'%port_id)
    nic.port = port 
    session.commit()
def connect_vlan(vlan_id,group_name,nic_name):
    vlan           = get_entity_by_cond(Vlan,'vlan_id==%d'%vlan_id)
    group          = get_entity_by_cond(Group,'group_name=="%s"'%group_name)
    vlan.nic_name  = nic_name
    vlan.group     = group
    vlan.available = False
    session.commit()


def create_vlan(vlan_id):
    print vlan_id
    try:
        vlan = Vlan(vlan_id)
        session.add(vlan)
        session.commit()
    except IntegrityError:
        raise DuplicateError('duplicate vlan #%d.' % vlan_id)

def add_node_to_group(node_id,group_name):

    node=get_entity_by_cond(Node,'node_id==%d'%node_id)
    group=get_entity_by_cond(Group,'group_name=="%s"'%group_name)
    try:
        if group.owner_name!=current_user and current_user!="admin":
            print 'access denied'
            return
        if node.available:
            node.group=group
            node.available=False
        else:
            raise NotAvailableError('Not available')
    except AttributeError:
        raise NotExistError('Either node %d or group %s does not exist'%(node_id,group_name))        
    session.commit()

def remove_node_from_group(node_id,group_name):
    node = get_entity_by_cond(Node, 'node_id==%d'%node_id)
    group = get_entity_by_cond(Group,'group_name=="%s"'%group_name)

    if group.owner_name!=current_user and current_user!="admin":
        print 'access denied'
        return

    if node.group_name != group_name:
        print 'node',node_id,'not in',group_name
        return
    node.group = None
    node.available = True




def create_group(group_name):
    group=Group(group_name)
    global current_user
    user = get_entity_by_cond(User,'user_name=="%s"'%current_user)
    group.owner = user
    session.add(group)
    session.commit()

def destroy_group(group_name):
    #ownership check
    group = get_entity_by_cond(Group,'group_name=="%s"'%group_name)
    if not group:
        print 'Group does not exist'
        return

    if current_user!="admin" and group_name.owner_name != current_user:
        print 'access denied'
        return

    for node in group.nodes:
        node.available = True
    group.nodes = []
    session.delete(group)
    session.commit()


def check_same_non_empty_list(ls):
    for ele in ls:
        if ele != ls[0]: return False
    return ls[0]

def deploy_group(group_name):
    group = get_entity_by_cond(Group,'group_name=="%s"'%group_name)
    
    vlan_id = group.vlans[0].vlan_id
    
    vm_name = group.vm.vm_name
    vm_node = haas.headnode.HeadNode(vm_name)
    vm_node.add_nic(vlan_id)
    vm_node.start()

    active_switch_str = cfg.get('general', 'active_switch')
    active_switch = sys.modules['haas.drivers.' + active_switch_str]

    for node in group.nodes:
        active_switch.set_access_vlan(node.nics[0].port.port_no, vlan_id)

def create_headnode():
    conn = haas.headnode.Connection()
    vm_node = conn.make_headnode()
    vm = VM(vm_node.name)
    print vm.vm_name
    session.add(vm)
    session.commit()

def attach_headnode(vm_name,group_name):
    group = get_entity_by_cond(Group,'group_name=="%s"'%group_name)
    vm = get_entity_by_cond(VM,'vm_name=="%s"'%vm_name)
    vm.available = False
    group.vm = vm
    session.commit()

def show_all():
    query_db(Node)
    query_db(NIC)
    query_db(Port)
    query_db(Vlan)
    query_db(VM)
    query_db(Switch)
    query_db(Group)
    query_db(User)
                                    
