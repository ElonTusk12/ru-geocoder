import pytest
from src.core.db_client import DBClient

@pytest.fixture
def db_client():
    return DBClient(db_path="tests/test_data/geocoder_test.db")

class TestDBClient:

    def test_db_client_context_manager(self, db_client):
        with db_client as db:
            result = db.search_addresses(["новосибирск", "ленина", "5"], )
            assert result is not None
            assert result["lat"] == 55.0302
            assert "новосибирская" in result["region"]


    def test_db_client_address_not_found(self, db_client):
        with db_client as db:
            result = db.search_addresses(["городакоторогонет", "лол"], )
            assert result is None


    def test_db_client_empty_tokens(self, db_client):
        result = db_client.search_addresses([], )
        assert result is None
