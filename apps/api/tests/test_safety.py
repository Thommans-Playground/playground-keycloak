"""The tests drop and recreate every table. They must never be able to do that to the app's own database."""

import pytest

from tests.safety import check_test_database


def test_a_database_named_for_tests_is_allowed():
    for url in ("postgresql+psycopg://u:p@localhost:5433/playground_test", "postgresql://u:p@db/anything_test"):
        assert check_test_database(url) == url


def test_the_apps_own_database_is_refused():
    for url in (
        "postgresql+psycopg://u:p@localhost:5433/playground",
        "postgresql://u:p@db/prod",
        "postgresql://u:p@db/",
    ):
        with pytest.raises(RuntimeError, match="_test"):
            check_test_database(url)
