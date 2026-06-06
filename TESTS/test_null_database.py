from unittest.mock import MagicMock

from DATABASE.database import Database, NullDatabase


def test_null_database_methods():
    nd = NullDatabase()
    assert nd.available() is False
    assert nd.create_analysis_run() == -1
    assert nd.get_findings() == []
    assert nd.get_findings_with_explanations() == []
    assert nd.insert_finding() is None

    # Test fallback __getattr__
    assert nd.some_random_method() is None
    assert nd.another_method(1, 2, a=3) is None


def test_database_available():
    db = Database()
    status = db.available()
    assert isinstance(status, bool)


def test_database_close():
    db = Database()
    mock_pool = MagicMock()
    Database._pool = mock_pool
    db.close()
    mock_pool.closeall.assert_called_once()
    assert Database._pool is None
