from haas.dev_support import no_dry_run
from haas.config import cfg
from haas.test_common import *


class TestNoDryRun:

    @clear_config_decorator
    def test_function(self):
        cfg.add_section('devel')
        cfg.set('devel', 'dry_run', True)

        @no_dry_run
        def func():
            assert False
        func()

    @clear_config_decorator
    def test_method(self):
        cfg.add_section('devel')
        cfg.set('devel', 'dry_run', True)

        class Cls:

            @no_dry_run
            def method(self):
                assert False
        obj = Cls()
        obj.method()
