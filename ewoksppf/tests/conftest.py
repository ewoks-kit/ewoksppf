import sys
import logging
import pytest
from . import test_ppf_actors

# loggers = [logging.getLogger("pypushflow"), logging.getLogger("ewoksppf")]
loggers = [logging.getLogger("ewoksppf")]

test_ppf_actors.SLEEP_TIME = 0


@pytest.fixture(scope="session")
def ppf_logging():
    stdouthandler = logging.StreamHandler(sys.stdout)
    levels = []
    for logger in loggers:
        levels.append(logger.getEffectiveLevel())
        logger.setLevel(logging.DEBUG)
        logger.addHandler(stdouthandler)

    yield

    for level, logger in zip(levels, loggers):
        logger.setLevel(level)
        logger.removeHandler(stdouthandler)
