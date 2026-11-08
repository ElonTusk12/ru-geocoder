import pytest
from src.core.db_client import DBClient
from src.exceptions import DatabaseConnectionError

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
        
        assert result == []

    def test_db_client_empty_tokens(self, db_client):
        result = db_client.search_addresses([], )
        assert result == []

    def test_db_client_search_by_org(self, db_client):
        tokens = ["сбербанк"]
        result = db_client.search_addresses(tokens)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["org"] == "сбербанк"
        assert "сбербанк" in result[0]["format_address"]

    def test_db_client_missing_db(self, tmp_path):
        non_exist_db = tmp_path / "non_exist.db"
        client = DBClient(db_path=str(non_exist_db))
        with pytest.raises(DatabaseConnectionError) as exc_info:
            with client:
                pass
        assert "python3 data/import_data.py" in str(exc_info.value)

    def test_db_client_missing_table(self, tmp_path):
        empty_db = tmp_path / "empty.db"
        import sqlite3
        conn = sqlite3.connect(empty_db)
        conn.close()

        client = DBClient(db_path=str(empty_db))
        with pytest.raises(DatabaseConnectionError) as exc_info:
            client.search_addresses(["москва"])
        assert "python3 data/import_data.py" in str(exc_info.value)

    def test_db_client_search_bm25(self, db_client):
        tokens = ["новосибирск", "ленина", "5"]
        result = db_client.search_bm25(tokens, number_of_address=1)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["lat"] == 55.0302
        assert "format_address" in result[0]
