import pytest
from src.core.db_client import DBClient

@pytest.fixture
def db_client():
    return DBClient(db_path="tests/test_data/geocoder_test.db")

class TestDBClient:

    def test_db_client_search_addresses_limit_one(self, db_client):
        tokens = ["новосибирск", "ленина", "5"]

        result = db_client.search_addresses(tokens, number_of_address=1)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["lat"] == 55.0302
        assert "format_address" in result[0]

    def test_db_client_search_addresses_default_limit(self, db_client):
        tokens = ["новосибирск", "ленина", "5"]

        result = db_client.search_addresses(tokens)
            
        assert isinstance(result, list)
        assert len(result) == 1

    def test_db_client_search_addresses_limit_exceed(self, db_client):
        tokens = ["москва"]
        
        result = db_client.search_addresses(tokens, number_of_address=10)
            
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_db_client_search_addresses_multiple(self, db_client):
        tokens = ["ленина"]
        
        result = db_client.search_addresses(tokens, number_of_address=2)
        
        assert isinstance(result, list)
        assert len(result) <= 2
        for item in result:
            assert "format_address" in item
            assert "lat" in item
            assert "lon" in item
    
    def test_db_client_address_not_found(self, db_client):
        tokens = ["городакоторогонет", "лол"]
        
        result = db_client.search_addresses(tokens, )
        
        assert result is None

    def test_db_client_empty_tokens(self, db_client):
        result = db_client.search_addresses([], )
        assert result is None
