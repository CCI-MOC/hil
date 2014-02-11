
from haas import control

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
        func(*match.group())
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

@command('group create (\w+)')
def create_group(group_name):
    control.create_group(group_name)

@command('node create (\d+)')
def create_node(node_id):
    control.create_node(node_id)

@command('nic create (\d+) (\w+) (\w+)')
def create_nic(nic_id, mac_addr, name):
    control.create_nic(int(nic_id), mac_addr, name)

@command('nic add (\d+) (\d+)')
def add_nic(nic_id, node_id):
    control.add_nic(int(nic_id), int(node_id))

@command('nic connect (\d+) (\d+)')
def connect_nic(nic_id, port_id):
    return control.connect_nic(nic_id, port_id)

@command('switch create (\d+) (\w+)')
def create_switch(switch_id, script)
    control.create_switch(int(switch_id), script)

create_port = re.compile('^port create (\d+) (\d+) (\d+)$')
connect_nic = re.compile('^nic connect (\d+) (\d+)$')
deploy_group = re.compile('^group deploy (\w+)$')
destroy_group = re.compile('^group destroy (\w+)$')
create_vlan = re.compile('^vlan create (\d+)$')
connect_vlan = re.compile('^vlan connect (\d+) (\w+) (\w+)$')
add_node = re.compile('^node add (\d+) (\w+)$')
create_node = re.compile('^node create (\d+)$')
change_head = re.compile('^change (\w+) head to (\S+)')
change_vlan = re.compile('^change (\w+) vlan to (\d+)')
show_table = re.compile('^show (\w+)')
show_free_table = re.compile('^show free (\w+)')
show_group = re.compile('^show group (\w+)')
destroy_vlan = re.compile('^destroy vlan (\d+)')
create_user = re.compile('^create user (\w+) (\w+)$')
remove = re.compile('^remove (\S+) from (\w+)$')

@command('headnode attach ([\w-]+) (\w+)');
def headnode_attach(vlan_id, group_name): pass

@command('exit')
def exit_cmd():
    raise _QuitException()

@command('help')
def usage():
    help_text='''
        node create <node_id>
        nic create <nic_id> <mac_addr> <name>
        nic add <nic_id> <node_id>
        switch create <switch_id> <script>
        port create <port_id> <switch_id> <port_no>
        nic connect <nic_id> <port_id>
        group create <group_name>
        vlan create <vlan_id>
        vlan connect <vlan_id> <group_name> <nic_name>
        node add <node_id> <group_name>
        headnode create
        headnode attach <vm_name> <group_name>
        group deploy <group_name>

        exit
        '''
    print help_text
