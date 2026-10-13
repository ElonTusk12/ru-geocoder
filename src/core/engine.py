from typing import Optional
import json
from src.core.db_client import DBClient
from src.core.parser import AddressParser
from src.exceptions import AddressParseError, AddressNotFoundError, GeocoderError
from rapidfuzz import fuzz, process


def address_process(tokens: dict[str, str]) -> str:
    """
    Составляет из токенов строку для сравнения улиц и домов
    """
    fields = [tokens.get("street"), tokens.get("house"), tokens.get("corp")]
    return " ".join([str(f) for f in fields if f is not None])


class GeocoderEngine:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.parser = AddressParser()

    def geocode(self, raw_address: str, number_of_addresses : int) -> Optional[list[dict]]:
        """
        Получает одну строку адреса.
        Возвращает словарь с форматированным адресом и координатами.
        """
        if not raw_address or not raw_address.strip():
            raise AddressParseError("Пустая строка адреса.")

        tokens = self.parser.parse_tokens(raw_address)
        if not tokens:
            raise AddressParseError(f"Некорректный формат адреса: {raw_address}")

        db_result = None

        with DBClient(self.db_path) as db:
            db_result = db.search_addresses(tokens, number_of_addresses * 10)

        if not db_result or len(db_result) == 0:
            raise AddressNotFoundError(f"Адрес '{raw_address}' не найден в базе данных.")
        
        return self.get_candidates(raw_address, db_result, number_of_addresses)

    def geocode_batch(self, input_path: str, output_path: str) -> None:
        """
        Пакетный режим обработки файлов
        Читает адреса из input_path и сохраняет результаты в output_path
        """
        try:
            with open(input_path, "r", encoding="utf-8") as infile, \
                    open(output_path, "w", encoding="utf-8") as outfile, \
                    DBClient(self.db_path) as db:

                for line in infile:
                    raw_address = line.strip()
                    if not raw_address:
                        continue

                    tokens = self.parser.parse_tokens(raw_address)
                    if not tokens:
                        out_data = {
                            "initial_address": raw_address,
                            "status": "parse_error"
                        }
                        json.dump(out_data, outfile, ensure_ascii=False)
                        outfile.write("\n")
                        continue

                    db_result = db.search_addresses(tokens, )

                    if db_result:
                        out_data = {
                            "initial_address": raw_address,
                            "status": "success",
                            "format_address": db_result["format_address"],
                            "address_components": {
                                "region": db_result["region"],
                                "city": db_result["city"],
                                "street": db_result["street"],
                                "house": db_result["house"]
                            },
                            "lat": db_result["lat"],
                            "lon": db_result["lon"]
                        }
                    else:
                        out_data = {
                            "initial_address": raw_address,
                            "status": "not_found"
                        }

                    json.dump(out_data, outfile, ensure_ascii=False)
                    outfile.write("\n")
        except FileNotFoundError:
            raise GeocoderError(f"Файл не найден: {input_path}")
        except IOError as e:
            raise GeocoderError(f"Ошибка ввода-вывода при работе с файлами: {e}")

    def get_candidates(self, query: str, choices : list[dict], number_of_candidates : int) -> list[dict]:
        """
        Выдает <= N адресов, похожих на query
        """
        s = self.parser.parse_structure(raw_text=query)
        results = process.extract(
            query = s,
            choices = choices,
            processor = address_process,
            limit = number_of_candidates,
        )
        return [x[0] for x in results]
        
        
        