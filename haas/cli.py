
from haas import control
import inspect

# A dictionary with names of commands (strings) as keys, and the
# corresponding `_Command` objects as values. See also `command`.
commands = {}

# This is used by the exit command to tell the main loop when to stop.
class _QuitException(Exception):
    pass


class BadCommandError(Exception):
    """raised by a `Command` object to indicate an invalid command"""
    pass

class _Command(object):
    """A shell command, such as `exit`, `create_nic`, `deploy_group`, etc."""

    def __init__(self, func, name=None):
        """Creates a command with `func` as the action to be performed.

        if `name` is specified, use it as the name by which the command will be
        invoked. otherwise, use `func.__name__`.
        """
        self.func = func
        if name:
            self.name = name
        else:
            self.name = func.__name__
        commands[self.name] = self

        self.arg_names = inspect.getargspec(func).args
        self.arg_count = len(self.arg_names)

    def _validate(self, text):
        """Verify that `text` is a valid invocation of this command.

        If `text` is invalid, `_validate` will raise a
        `BadCommandError`, with a message describing the problem.
        otherwise, it will return normally.
        """
        parts = text.split()

        # Make sure we were invoked by the correct name. This should *always* be
        # the case, no matter what the user inputs.
        assert parts[0] == self.name, 'BUG: command invoked by wrong name.'

        if len(parts) != self.arg_count + 1:
            # `parts` should have one more element than the number of
            # expected arguments (which will be the command name).
            raise BadCommandError('%s : Wrong number of arguments.' % self.name)

    def invoke(self, text):
        """Invoke the command with text `text`.

        Raise a BadCommandError if the command is invalid.
        """
        self._validate(text)
        parts = text.split()
        self.func(*parts[1:])

    def usage(self):
        """Displays a usage summary for this command."""
        print "   ", self.name, ' '.join(map(lambda x: '<%s>' % x, self.arg_names))


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
        _Command(func, name=name)
        return func
    return register

def run_command(text):
    """Run the command specified in the string `text`.

    if `text` is not a valid command, display a help message to the user.
    """
    parts = text.split()
    if len(parts) == 0: # empty command
        return
    if parts[0] not in commands:
        print('Invalid command.')
        usage()
    else:
        try:
            cmd = commands[parts[0]]
            cmd.invoke(text)
        except BadCommandError, e:
            print e.message
            usage()

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
    control.create_group(group_name)

@command()
def create_node(node_id):
    control.create_node(node_id)

@command()
def add_node(node_id,group_name):
    control.add_node_to_group(int(node_id),group_name)

@command()
def create_nic(nic_id, mac_addr, name):
    control.create_nic(int(nic_id), mac_addr, name)

@command()
def connect_nic(nic_id, port_id):
    control.connect_nic(int(nic_id), int(port_id))

@command()
def add_nic(nic_id, node_id):
    control.add_nic(int(nic_id), int(node_id))

@command()
def create_switch(switch_id, script):
    control.create_switch(int(switch_id), script)

@command()
def create_port(port_id,switch_id,port_no):
    control.create_port(int(port_id),int(switch_id),int(port_no))
    
@command()
def create_vlan(vlan_id):
    control.create_vlan(int(vlan_id))
    
@command()
def connect_vlan(vlan_id,group_name,nic_name):
    control.connect_vlan(int(vlan_id),group_name,nic_name)

@command()
def headnode_create():
    control.create_headnode()

@command()
def headnode_attach(vm_name, group_name):
    control.attach_headnode(vm_name,group_name)

@command()
def deploy_group(group_name):
    control.deploy_group(group_name)
    
@command()
def create_user(user_name,password):
    control.create_user(user_name,password)

@command()
def show_all():
    control.show_all()

@command('show')
def show_table(table_name):
    """show [ group | vm | port | nic | vlan | switch | node | user ]"""
    control.show_table(table_name)


@command('help')
def usage():
    print "------- commands --------"
    names = commands.keys()
    names.sort()
    for cmd_name in names:
        cmd = commands[cmd_name]
        cmd.usage()
    print "------ notes ------------"
    print " port_id - global number for port on switch"
    print " port_no - switch specific number of port"


@command('exit')
def exit_cmd():
    print 'Bye for now.'
    raise _QuitException()
