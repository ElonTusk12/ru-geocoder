import re

class AddressParser:
    def __init__(self):
        self.garbage_pattern = re.compile(r'\b(г|город|ул|улица|д|дом|к|корп|корпус|кв|квартира|обл|область)\b\.?', re.IGNORECASE)

    def parse(self, raw_text: str) -> list[str]:
        if not raw_text:
            return None

        address = raw_text.lower()
        address = re.sub(r'[,.\-/]', ' ', address)
        address = self.garbage_pattern.sub('', address)
        tokens = address.split()

        return tokens