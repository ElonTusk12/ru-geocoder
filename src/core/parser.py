import re

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
    def parse(self, raw_text: str) -> list[str]:
        """
        Очищает строку и разбивает её на токены для FTS5.
        """
        if not raw_text:
            return []

        address = self.punctuation_pattern.sub(' ', raw_text.lower())

        tokens = [token for token in address.split() if token not in self.garbage_words]

        return tokens
