"""Tests performing linter-like checks"""

import ast
from os.path import dirname, join
from subprocess import check_output


# Root of the repository. Note that this is relative to this file,
# so if this file is moved, this may need to be changed:
source_root = dirname(dirname(__file__))


def test_logger_format_strings():
    """Scan for proper use of logger format strings

    Per @zenhack's comment on issue #629:

    > All over the codebase you can find statments like:
    >
    >   logger.error('Foo: %r' % bar)
    >
    > The % operator being python's format-string splicing operator. The
    > problem with this is that the logging functions do the formation
    > string splicing themselves, i.e. what you want in this case is:
    >
    >   logger.error('Foo: %r', bar)
    >
    > This opens up the possibility of format-string injection
    > vulnerabilities. Frankly, this is too easy to do, especially
    > since in other contexts % is the correct thing. We ought to
    > (a) make sure all instances of this mistake are fixed, and (b)
    > come up with a way to catch this mistake automatically going
    > forward; perhaps some kind of linter.

    This is that linter; it scans the source tree looking for places
    where the logging functions are called with any first argument
    that isn't a string literal.
    """

    files = check_output([join(source_root, 'ci', 'list_tracked_pyfiles.sh')])\
        .strip().split('\n')

    for filename in files:
        with open(join(source_root, filename)) as f:
            tree = ast.parse(f.read(), filename=filename)
        LogCallVisitor(filename).visit(tree)


class LogCallVisitor(ast.NodeVisitor):
    """Ast node visitor used by test_logger_format_strings."""

    def __init__(self, filename):
        self.filename = filename

    def visit_Call(self, node):
        logfunc_names = {
            'critical', 'error', 'warn', 'info', 'debug',
        }

        # Make sure this is a call to one of the logging methods.
        # NOTE: we're going based on the method name only; in theory
        # this could give us false positives if someone names another
        # function after one of these, or false negatives if we store
        # one of these in a variable (don't do that). We could be
        # smarter about figuring out what function is being called,
        # but this is probably good enough.
        if isinstance(node.func, ast.Attribute):
            # This is a method call on on object. visit_Call is invoked
            # on every call expression in the AST, including plain-old
            # functions, and computed functions like
            # `myfunctable[23](...)`. We only want to process nodes of
            # the form foo.bar(...).
            funcname = node.func.attr
        else:
            return
        if funcname not in logfunc_names:
            return

        # We've decided this is a logging call; sanity check it:
        assert len(node.args) != 0, (
            "Logging function called with zero arguments at %r "
            "line %d column %d." % (self.filename,
                                    node.lineno,
                                    node.col_offset)
        )
        assert isinstance(node.args[0], ast.Str), (
            "Logging function called with non-string literal format "
            "string at %r line %d column %d." % (self.filename,
                                                 node.lineno,
                                                 node.col_offset)
        )
