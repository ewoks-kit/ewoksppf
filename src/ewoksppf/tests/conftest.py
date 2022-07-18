import pytest
from pypushflow import persistence
from . import test_ppf_actors

test_ppf_actors.SLEEP_TIME = 0


@pytest.fixture(scope="session")
def ppf_log_config():
    DEFAULT_DB_TYPE = persistence.DEFAULT_DB_TYPE
    persistence.DEFAULT_DB_TYPE = "memory"
    yield
    persistence.DEFAULT_DB_TYPE = DEFAULT_DB_TYPE
