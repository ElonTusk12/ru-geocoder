from src.core.parser import AddressParser


def test_successful_parse():
    parser = AddressParser()

    result = parser.parse_tokens("г. Москва, ул. Ленина, д. 15")
    assert result == ["москва", "ленина", "15"]

    result = parser.parse_tokens("МСК, УЛ. КРАСНАЯ, д.10-к2")
    assert result == ["мск", "красная", "10", "к2"]


def test_empty_address():
    parser = AddressParser()

    assert parser.parse_tokens("") == []
    assert parser.parse_tokens("   ") == []