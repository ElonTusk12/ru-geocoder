import re
from typing import Any


class AddressParser:
    def __init__(self):
        self.garbage_words = {
            'г', 'город', 'ул', 'улица', 'д', 'дом', 'обл', 'область',
            'респ', 'республика', 'кр', 'край', 'пос', 'поселок', 'с', 'село',
            'пер', 'переулок', 'проспект', 'пр', 'пр-кт', 'ш', 'шоссе',
            'к', 'корп', 'корпус', 'стр', 'строение', 'вл', 'владение',
            'кв', 'квартира', 'оф', 'офис'
        }
        self.punctuation_pattern = re.compile(r'[.,\-/\\()]')

        self.house_pattern = re.compile(r'(?:д|дом)\b\s*(\d+[а-я]?(?:/\d+)?)|\b(\d+[а-я]?)$')
        self.corp_pattern = re.compile(r'(?:к|корп|корпус)\b\s*(\d+[а-я]?)')
        self.street_pattern = re.compile(r'(?:ул|улица|проспект|пр|пр-кт|ш|шоссе|пер|переулок)\b\s*'
                                         r'('
                                         r'[а-яё\-]+(?:\s[а-яё\-]+)*'
                                         r'|'
                                         r'\d+\s+[а-яё\-]+(?:\s+[а-яё\-]+)*'
                                         r')'
                                         )
    def parse_tokens(self, raw_text: str) -> list[str]:
        """
        Очищает строку и разбивает её на токены для FTS5.
        """
        if not raw_text:
            return []

        raw_text_clean = self.punctuation_pattern.sub(' ', raw_text.lower())

        return [token for token in raw_text_clean.split() if token not in self.garbage_words]
    def parse_structure(self, raw_text: str) -> dict[str, str]:
        """
        Парсит строку для ранжирования rapidfuzz
        """
        raw_text_clean = self.punctuation_pattern.sub(' ', raw_text.lower())

        house_match = self.house_pattern.search(raw_text_clean)
        corp_match = self.corp_pattern.search(raw_text_clean)
        street_match = self.street_pattern.search(raw_text_clean)

        return {
            'house': (house_match.group(1) or house_match.group(2)) if house_match else '',
            'corp': corp_match.group(1) if corp_match else '',
            'street': street_match.group(1) if street_match else '',
        }
        
        
