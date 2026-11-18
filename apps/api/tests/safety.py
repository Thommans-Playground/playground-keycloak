"""A guard for TEST_DATABASE_URL: the tests drop all tables first, so only a database made for tests may be used."""

from sqlalchemy.engine import make_url


def check_test_database(url: str) -> str:
    name = make_url(url).database or ""
    if not name.endswith("_test"):
        raise RuntimeError(
            f"Refusing to run the tests on database '{name}': they drop every table first. "
            "Use a database whose name ends in _test, for example playground_test."
        )
    return url
