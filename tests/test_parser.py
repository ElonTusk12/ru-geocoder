import pytest

from src.core.parser import AddressParser

class TestAddressParser:
    parser = AddressParser()
    
    @pytest.mark.parametrize(
        "raw_text, expected_result",
        [
            ('г. Москва, ул. Ленина, д. 15', ["москва", "ленина", "15"]),
            ("МСК, УЛ. КРАСНАЯ, д.10-к2", ["мск", "красная", "10", "к2"]),
        ]
    )
    def test_successful_parse(self, raw_text : str, expected_result : list[str]):
    
        result = self.parser.parse_tokens(raw_text)
        assert result == expected_result
        
    @pytest.mark.parametrize(
        "raw_text, expected_result",
        [
            ('', []),
            ("      ", []),
            ("-()(.", []),
        ]
    )
    def test_strange_parse(self, raw_text : str, expected_result : list[str]):

        result = self.parser.parse_tokens(raw_text)
        assert result == expected_result
        
    @pytest.mark.parametrize(
        "raw_text, expected_result",
        [
            ('г. Москва, ул. Ленина, д. 15', ["15", "ленина", ""]),
            ("МСК, УЛ. КРАСНАЯ-ЖЕЛТАЯ, д.10-к2", ["10", "красная желтая", ""]),
            ("МСК, проспект. КРАСНый, д.10-к2 корп 6", ["10", "красный", "6"]),
            ("МСК,  д.10-к2 корп 6", ["10", "", "6"]),
            ("", ["","",""])
        ]
    )
    def test_successful_structure(self, raw_text : str, expected_result : list[str]):
        
        result = self.parser.parse_structure(raw_text)
  
        assert len(result) == 3
        assert result['house'] == expected_result[0]
        assert result['street'] == expected_result[1]
        assert result['corp'] == expected_result[2]

    @pytest.mark.parametrize(
        "raw_text, expected_result",
        [
            ("г. Омск, Омская область", ["", "", ""]),
            ("", ["","",""]),
            ("-()/.", ["","",""])
        ]
    )
    def test_strange_structure(self, raw_text : str, expected_result : list[str]):
        
        result = self.parser.parse_structure(raw_text)
        
        assert len(result) == 3
        assert result['house'] == expected_result[0]
        assert result['street'] == expected_result[1]
        assert result['corp'] == expected_result[2]