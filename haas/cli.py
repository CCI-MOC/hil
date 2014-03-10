
from haas import control
import inspect

# A dictionary with names of commands (strings) as keys, and the corresponding
# functions as values. See the `command` decorator, below, for details.
commands = {}


# This is used by the exit command to tell the main loop when to stop.
class _QuitException(Exception): pass

def command(name=None):
    """`command` is a decorator used to define shell commands.

        @command()
        def do_foo(x,y,z):
            ...

    Will register a command named `do_foo`, which expects three arguments, and
    invokes the function do_foo when executed. when the help command is
    executed, the string "do_foo <x> <y> <z>" will be shown.

    An optional parameter may be provided, which will override the name of the
    command. This is useful (for example) when the command has the same name as
    a standard python function:

        @command('help')
        def usage():
            ...

    This decorator does not modify its argument.
    """
    def register(func):
        if name:
            commands[name] = func
        else:
            commands[func.__name__] = func
        return func
    return register

def run_command(cmd):
    """Run the command specified in the string `cmd`.

    if `cmd` is not a valid command, display a help message to the user.
    """
    parts = cmd.split()
    if parts[0] not in commands:
        print('Invalid command.')
        usage()
    else:
        func = commands[parts[0]]
        func(*parts[1:])

def main_loop():
    """Runs the interactive command interpreter.

    Repeatedly prompts the user for commands and executes them. displays
    usage information if an invalid command is entered, and stops when
    the `exit` command is executed, or end of file is reached.
    """
    try:
        while True:
            cmd = raw_input('haas> ')
            run_command(cmd)
    except _QuitException:
        pass
    except EOFError:
        # We should exit cleanly on EOF
        pass

@command()
def create_group(group_name):
    """group create <group_name>"""
    control.create_group(group_name)

@command()
def create_node(node_id):
    """node create <node_id>"""
    control.create_node(node_id)

@command()
def add_node(node_id,group_name):
    """node add <node_id> <group_name>"""
    control.add_node_to_group(int(node_id),group_name)

@command()
def create_nic(nic_id, mac_addr, name):
    """nic create <nic_id> <mac_addr> <name>"""
    control.create_nic(int(nic_id), mac_addr, name)

@command()
def connect_nic(nic_id, port_id):
    """nic connect <nic_id> <port_id>"""
    control.connect_nic(int(nic_id), int(port_id))

@command()
def add_nic(nic_id, node_id):
    """nic add <nic_id> <node_id>"""
    control.add_nic(int(nic_id), int(node_id))

@command()
def create_switch(switch_id, script):
    """switch create <switch_id> <script>"""
    control.create_switch(int(switch_id), script)

@command()
def create_port(port_id,switch_id,port_no):
    """port create <port_id> <switch_id> <port_no>"""
    control.create_port(int(port_id),int(switch_id),int(port_no))
    
@command()
def create_vlan(vlan_id):
    """vlan create <vlan_id>"""
    control.create_vlan(int(vlan_id))
    
@command()
def connect_vlan(vlan_id,group_name,nic_name):
    """vlan connect <vlan_id> <group_name> <nic_name>"""
    control.connect_vlan(int(vlan_id),group_name,nic_name)

@command()
def headnode_create():
    """headnode create"""
    control.create_headnode()

@command()
def headnode_attach(vm_name, group_name):
    """headnode attach <vm_name> <group_name>"""
    control.attach_headnode(vm_name,group_name)

@command()
def deploy_group(group_name):
    """group deploy <group_name>"""
    control.deploy_group(group_name)
    
@command()
def create_user(user_name,password):
    """user create <user name> <password>"""
    control.create_user(user_name,password)

@command()
def show_all():
    """show all"""
    control.show_all()

@command('show')
def show_table(table_name):
    """show [ group | vm | port | nic | vlan | switch | node | user ]"""
    control.show_table(table_name)

@command('help')
def usage():
    """help"""
    print "------- commands --------"
    names = commands.keys()
    names.sort()
    for cmd_name in names:
        func = commands[cmd_name]
        arg_names = inspect.getargspec(func).args
        print "   ", cmd_name, ' '.join(map(lambda x: '<%s>' % x, arg_names))
    print "------ notes ------------"
    print " port_id - global number for port on switch"
    print " port_no - switch specific number of port"


@command('exit')
def exit_cmd():
    """exit"""
    print 'Bye for now.'
    raise _QuitException()
