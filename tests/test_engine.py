import pytest
from src.core.db_client import DBClient

def test_db_client_context_manager():
    with DBClient(db_path="data/geocoder.db") as db:
        result = db.search_address(["новосибирск", "ленина", "5"])
        assert result is not None
        assert result["lat"] == 55.0302
        assert "Новосибирская" in result["format_address"]

def test_db_client_address_not_found():
    with DBClient(db_path="data/geocoder.db") as db:
        result = db.search_address(["городакоторогонет", "лол"])
        assert result is None

def test_db_client_empty_tokens():
    db = DBClient(db_path="data/geocoder.db")
    result = db.search_address([])
    assert result is None