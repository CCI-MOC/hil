from haas.model import *
from haas import config
import haas.control

@config.option('file_names')
def validate_file_names(file_names):
    if not isinstance(file_names, dict):
        raise config.ConfigError("`file_names` is not a dictionary.")
    required_files = [
        'node',
        'network',
        'vm',
        'switch',
        'port',
        'connect',
        'user',
    ]
    for filename in required_files:
        if filename not in file_names:
            raise config.ConfigError(
                'option `file_names` is missing `%s`' % filename)

        if not isinstance(file_names[filename], basestring):
            raise config.ConfigError(
                'option `file_names.%s` is not a string.' % filename)
        

def create_node_pool():
    keys=['node_id','mac_addr','manage_ip']
    with open(config.get('file_names')["node"]) as file:
        for line in file:
            values=line.rstrip().split(' ')
            d=dict(zip(keys,values))
            session.add(Node(int(d['node_id']),d['mac_addr'],d['manage_ip']))
    session.commit()

def create_network_pool():
    keys=['network_id','network_technology']
    with open(config.get('file_names')["network"]) as file:
        for line in file:
            values=line.rstrip().split(" ")
            d=dict(zip(keys,values))
            session.add(Network(int(d["network_id"]),d["network_technology"]))
    session.commit()

def create_vm_pool():
    keys=['vm_name']
    with open(config.get('file_names')["vm"]) as file:
        for line in file:
            values = line.rstrip().split(" ")
            d = dict(zip(keys,values))
            session.add(VM(d["vm_name"]))
    session.commit()


def create_switch_pool():
    keys=["switch_id","script"]
    with open(config.get('file_names')["switch"]) as file:
        for line in file:
            values = line.rstrip().split(" ")
            d = dict(zip(keys,values))
            session.add(Switch(int(d["switch_id"]),d["script"]))
    session.commit()

def create_port_pool():
    keys=["port_id","switch_id","port_no"]
    with open(config.get('file_names')["port"]) as file:
        for line in file:
            values = line.rstrip().split(" ")
            d = dict(zip(keys,values))
            session.add(Port(int(d["port_id"]),int(d["switch_id"]),int(d["port_no"])))
    session.commit()

def connect_node_to_port():

    keys=["node_id","port_id"]
    with open(config.get('file_names')["connect"]) as file:
        for line in file:
            values = line.rstrip().split(" ")
            d=dict(zip(keys,values))
            node=haas.control.get_entity_by_cond(Node,"node_id==%d"%int(d["node_id"]))
            port=haas.control.get_entity_by_cond(Port,"port_id==%d"%int(d["port_id"]))
            node.port=port
    session.commit()

def add_users():
    keys=["user_name","password","user_type"]
    with open(config.get('file_names')["user"]) as file:
        for line in file:
            values = line.rstrip().split(" ")
            d = dict(zip(keys,values))
            session.add(User(d["user_name"],d["password"],d["user_type"]))
    session.commit()

def load_resources():
#    create_node_pool()
#    create_network_pool()
#    create_vm_pool()
#    create_switch_pool()
#    create_port_pool()
#    connect_node_to_port()
    add_users()

if __name__=='__main__':
    haas.config.load()
    load_resources()
