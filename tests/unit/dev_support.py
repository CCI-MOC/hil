from haas.dev_support import no_dry_run
from haas.config import cfg

cfg.add_section('devel')
cfg.set('devel', 'dry_run', True)


class TestNoDryRun:

    def test_function(self):
        @no_dry_run
        def func():
            assert False
        func()

    def test_method(self):
        class Cls:

            @no_dry_run
            def method(self):
                assert False
        obj = Cls()
        obj.method()
