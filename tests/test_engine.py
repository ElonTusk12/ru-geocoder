import pytest
import json

from src.core.db_client import DBClient
from src.exceptions import *
from src.core.engine import GeocoderEngine

DB_CLIENT = DBClient(db_path="tests/test_data/geocoder_test.db")
@pytest.fixture
def engine():
    return GeocoderEngine(db_client=DB_CLIENT)

class TestEngine:

    def test_geocoder_successful_geocode(self, engine):
        result = engine.geocode("г. Москва, ул. Ленина, д. 15")
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["lat"] == 55.7558
        assert result[0]["lon"] == 37.6173
        assert "московская" in result[0]["region"]
        assert "москва" in result[0]["city"]
        assert "15" in result[0]["house"]

    def test_geocoder_multiple_addresses(self, engine):
        result = engine.geocode("ленина", number_of_addresses=2)
        assert isinstance(result, list)
        assert len(result) <= 2
        assert len(result) > 0
        
    def test_geocoder_multiple_orgs(self, engine):
        result = engine.geocode("омск чапаева")
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "аптека" in result[0]["orgs"]
        assert "втб" in result[0]["orgs"]
    def test_geocoder_address_not_found(self, engine):
        with pytest.raises(AddressNotFoundError):
            engine.geocode("городакоторогонет, ул. Ленина, д. 5")

    def test_geocoder_garbage(self, engine):
        with pytest.raises(AddressParseError):
            engine.geocode("город ул улица д дом")

    def test_geocoder_empty_address(self, engine):
        with pytest.raises(AddressParseError):
            engine.geocode("   ")

    def test_geocoder_incorrect_format(self, engine):
        with pytest.raises(AddressNotFoundError): #тут еще надо подумать
            engine.geocode("некорректный адрес")

class TestBatchEngine:
    
    def test_geocoder_batch_basic(self, engine, tmp_path):
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text(
            "г. Новосибирск, ул. Ленина, дом 5\n"
            "мусорный адрес\n"
            ",.,.,\n",
            encoding="utf-8"
        )

        engine.geocode_batch(str(input_file), str(output_file))

        lines = output_file.read_text(encoding="utf-8").strip().splitlines()

        data_1 = json.loads(lines[0])
        assert data_1["status"] == "success"
        assert data_1["initial_address"] == "г. Новосибирск, ул. Ленина, дом 5"
        assert data_1["address_components"]["city"] == "новосибирск"
        assert data_1["lat"] == 55.0302
        assert data_1["lon"] == 82.9204

        data_2 = json.loads(lines[1])
        assert data_2["status"] == "not_found"
        assert data_2["initial_address"] == "мусорный адрес"

        data_3 = json.loads(lines[2])
        assert data_3["status"] == "parse_error"
        assert data_3["initial_address"] == ",.,.,"

    def test_geocoder_batch_multiple_addresses(self, engine, tmp_path):
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text("ленина\n", encoding="utf-8")

        engine.geocode_batch(str(input_file), str(output_file), number_of_addresses=2)

        lines = output_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) <= 2
        assert len(lines) > 0
        for line in lines:
            data = json.loads(line)
            assert data["status"] == "success"

    def test_engine_batch_file_not_found(self, engine):
        with pytest.raises(GeocoderError):
            engine.geocode_batch("non_exist.txt", "output.txt")



