
from haas import control
import re

# A list of tuples of the form `(matcher, func)`, where `func` is a
# function to run when a command matching matcher is executed. Commands
# are added via the command decorator
commands = []


# This is used by the exit command to tell the main loop when to stop.
class _QuitException(Exception): pass

def command(pattern):
    """`command` is a decorator used to define shell commands.

    Defining a command looks like:

        @command('example command ([a-z]+) ([0-9]+)')
        def example_command(word, number):
            ...

    `pattern` should be a regex pattern which matches the desired
    command syntax. The pattern must match the whole command, which must
    fit on a single line - the pattern `create foo` will not match the
    command string `prefix create foo` or `create foo suffix`.

    Subexpressions enclosed in parentheses will be passed to the
    function as positional arguments when the command is executed.

    The docstring of each command will be displayed as part of the help
    message.

    This decorator does not modify its argument.
    """
    pattern = '^' + pattern + '$'
    matcher = re.compile(pattern)
    def register(func):
        commands.append((matcher, func))
        return func
    return register

def run_command(args):
    """Runs the command specified in the string `args`.

    returns `False` if the argument is not a valid command, and `True`
    otherwise.
    """
    for matcher, func in commands:
        match = matcher.match(args)
        if not match:
            continue
        func(*match.groups())
        return True
    return False 

def usage():
    pass

def main_loop():
    """Runs the interactive command interpreter.

    Repeatedly prompts the user for commands and executes them. displays
    usage information if an invalid command is entered, and stops when
    the `exit` command is executed.
    """
    try:
        while True:
            cmd = raw_input('haas> ')
            if not run_command(cmd):
                print "Invalid command."
                usage()
    except _QuitException:
        pass
    except EOFError:
        # We should exit cleanly on EOF
        pass

@command('group create (\w+)')
def create_group(group_name):
    """group create <group_name>"""
    control.create_group(group_name)

@command('node create (\d+)')
def create_node(node_id):
    """node create <node_id>"""
    control.create_node(node_id)

@command('node add (\d+) (\w+)')
def add_node(node_id,group_name):
    """node add <node_id> <group_name>"""
    control.add_node_to_group(int(node_id),group_name)

@command('nic create (\d+) (\w+) (\w+)')
def create_nic(nic_id, mac_addr, name):
    """nic create <nic_id> <mac_addr> <name>"""
    control.create_nic(int(nic_id), mac_addr, name)

@command('nic connect (\d+) (\d+)')
def connect_nic(nic_id, port_id):
    """nic connect <nic_id> <port_id>"""
    control.connect_nic(int(nic_id), int(port_id))

@command('nic add (\d+) (\d+)')
def add_nic(nic_id, node_id):
    """nic add <nic_id> <node_id>"""
    control.add_nic(int(nic_id), int(node_id))

@command('switch create (\d+) (\w+)')
def create_switch(switch_id, script):
    """switch create <switch_id> <script>"""
    control.create_switch(int(switch_id), script)

@command('port create (\d+) (\d+) (\d+)')
def create_port(port_id,switch_id,port_no):
    """port create <port_id> <switch_id> <port_no>"""
    control.create_port(int(port_id),int(switch_id),int(port_no))
    
@command('vlan create (\d+)')
def create_vlan(vlan_id):
    """vlan create <vlan_id>"""
    control.create_vlan(int(vlan_id))
    
@command('vlan connect (\d+) (\w+) (\w+)')
def connect_vlan(vlan_id,group_name,nic_name):
    """vlan connect <vlan_id> <group_name> <nic_name>"""
    control.connect_vlan(int(vlan_id),group_name,nic_name)

@command('headnode create')
def headnode_create():
    """headnode create"""
    control.create_headnode()

@command('headnode attach ([\w-]+) (\w+)')
def headnode_attach(vm_name, group_name):
    """headnode attach <vm_name> <group_name>"""
    control.attach_headnode(vm_name,group_name)

@command('group deploy (\w+)')
def deploy_group(group_name):
    """group deploy <group_name>"""
    control.deploy_group(group_name)
    
@command('user create (\w+) (\w+)')
def create_user(user_name,password):
    """user create <user name> <password>"""
    control.create_user(user_name,password)

@command('show all')
def show_all():
    """show all"""
    control.show_all()

@command('show (\w+)')
def show_table(table_name):
    """show [ group | vm | port | nic | vlan | switch | node | user ]"""
    control.show_table(table_name)

@command('help')
def usage():
    """help"""
    print "------- commands --------"
    for _, func in commands:
        print "   ", func.__doc__
    print "------ notes ------------"
    print " port_id - global number for port on switch"
    print " port_no - switch specific number of port"


@command('exit')
def exit_cmd():
    """exit"""
    print 'Bye for now.'
    raise _QuitException()
