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
        