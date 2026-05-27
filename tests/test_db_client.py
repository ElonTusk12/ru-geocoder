import pytest


from src.core.db_client import DBClient

class TestDBClient:
    @staticmethod
    def db_client():
        return DBClient(db_path="data/geocoder_test.db")

    def test_db_client_context_manager(self):
        with self.db_client() as db:
            result = db.search_address(["новосибирск", "ленина", "5"])
            assert result is not None
            assert result["lat"] == 55.0302
            assert "новосибирская" in result["region"]


    def test_db_client_address_not_found(self):
        with self.db_client() as db:
            result = db.search_address(["городакоторогонет", "лол"])
            assert result is None


    def test_db_client_empty_tokens(self):
        result = self.db_client().search_address([])
        assert result is None
