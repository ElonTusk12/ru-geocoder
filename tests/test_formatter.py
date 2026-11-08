import pytest
from src.core.formatter import format_address


import pytest


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        pytest.param(
            {
                "region": "Московская область",
                "city": "Москва",
                "street": "Ленина",
                "house": "15",
                "org": "Сбербанк",
            },
            "Сбербанк, Московская область, г. Москва, ул. Ленина, д. 15",
            id="full",
        ),
        pytest.param(
            {
                "region": "Новосибирская область",
                "city": "Новосибирск",
                "street": "Красный проспект",
                "house": "1",
            },
            "Новосибирская область, г. Новосибирск, ул. Красный проспект, д. 1",
            id="without_org",
        ),
        pytest.param(
            {
                "region": "Москва",
                "street": "Арбат",
            },
            "Москва, ул. Арбат",
            id="partial",
        ),
        pytest.param(
            {
                "city": "Омск",
                "street": "Ленина",
                "house": "5",
            },
            "г. Омск, ул. Ленина, д. 5",
            id="empty_region",
        ),
    ],
)
def test_format_address(kwargs, expected):
    assert format_address(**kwargs) == expected


def test_format_address_all_empty():
    assert format_address() == ""
