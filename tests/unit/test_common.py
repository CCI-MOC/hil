"""Self-tests for the test_common module."""


import pytest
import logging
from haas.test_common import fail_on_log_warnings, LoggedWarningError

fail_on_log_warnings = pytest.fixture(autouse=True)(fail_on_log_warnings)

haas_logger_names = ['haas', 'haas.rest', 'haas.foobar']
non_haas_logger_names = ['foo', 'bar', 'quux', 'argparse']


@pytest.mark.parametrize('level,loggername', [
    (level, loggername)
    for level in ['warn', 'error', 'critical']
    for loggername in ['haas', 'haas.rest', 'haas.foobar']
])
def test_should_raise(level, loggername):
    """Raise an exception if haas logs at or above warning level."""
    logger = logging.getLogger(loggername)
    logfn = getattr(logger, level)
    with pytest.raises(LoggedWarningError):
        logfn('Something bad happened!')


@pytest.mark.parametrize('level,loggername', [
    (level, loggername)
    for level in ['debug', 'info']
    for loggername in haas_logger_names
])
def test_no_raise_low_leve(level, loggername):
    """Don't raise an exception at info level or lower."""
    logger = logging.getLogger(loggername)
    logfn = getattr(logger, level)
    logfn('Nothing to worry about')


@pytest.mark.parametrize('level,loggername', [
    (level, loggername)
    for level in ['debug', 'info', 'warn', 'error', 'critical']
    for loggername in non_haas_logger_names
])
def test_no_raise_non_haas(level, loggername):
    """Don't raise an exception if some non-haas library logs warnings."""
    logger = logging.getLogger(loggername)
    logfn = getattr(logger, level)
    logfn("Somebody else's bug.")


def test_dont_pollute_other_tests_extensions():
    """Regression test for #697."""
    import sys
    for name in sys.modules.keys():
        assert not name.startswith('haas.ext.'), (
            "No extensions should have been loaded, but %r was. This may "
            "mean that tests are polluting each others' set of loaded "
            "extensions." % name
        )
