from typing import Optional
import json
from src.core.db_client import DBClient
from src.core.parser import AddressParser
from src.core.formatter import format_address
from src.exceptions import AddressParseError, AddressNotFoundError, GeocoderError


class GeocoderEngine:
    def __init__(self, parser: Optional[AddressParser] = None, db_client: Optional[DBClient] = None) -> None:
        self.parser = parser or AddressParser()
        self.db_client = db_client or DBClient()
    def geocode(self, raw_address: str, number_of_addresses: int = 1) -> Optional[list[dict]]:
        """
        Получает одну строку адреса.
        Возвращает список словарей с форматированным адресом и координатами.
        """
        if not raw_address or not raw_address.strip():
            raise AddressParseError("Пустая строка адреса.")

        tokens = self.parser.parse_tokens(raw_address)
        if not tokens:
            raise AddressParseError(f"Некорректный формат адреса: {raw_address}")

        with self.db_client as db:
            db_result = db.search_addresses(tokens, number_of_addresses * 10)

        if not db_result:
            raise AddressNotFoundError(f"Адрес '{raw_address}' не найден в базе данных.")

        return self._aggregate_results(db_result, number_of_addresses)

    def geocode_batch(self, input_path: str, output_path: str, number_of_addresses: int = 1) -> None:
        """
        Пакетный режим обработки файлов
        Читает адреса из input_path и сохраняет результаты в output_path
        """
        try:
            with open(input_path, "r", encoding="utf-8") as in_file, \
                    open(output_path, "w", encoding="utf-8") as out_file, \
                    self.db_client as db:

                for line in in_file:
                    raw_address = line.strip()
                    if not raw_address:
                        continue

                    tokens = self.parser.parse_tokens(raw_address)
                    if not tokens:
                        out_data = {
                            "initial_address": raw_address,
                            "status": "parse_error"
                        }
                        json.dump(out_data, out_file, ensure_ascii=False)
                        out_file.write("\n")
                        continue

                    db_result = db.search_addresses(tokens, number_of_addresses * 10)

                    if db_result:
                        candidates = self._aggregate_results(db_result, number_of_addresses)
                        for result in candidates:
                            out_data = {
                                "initial_address": raw_address,
                                "status": "success",
                                "format_address": result["format_address"],
                                "address_components": {
                                    "region": result["region"],
                                    "city": result["city"],
                                    "street": result["street"],
                                    "house": result["house"],
                                    "orgs": result["orgs"],
                                },
                                "lat": result["lat"],
                                "lon": result["lon"]
                            }
                            json.dump(out_data, out_file, ensure_ascii=False)
                            out_file.write("\n")
                    else:
                        out_data = {
                            "initial_address": raw_address,
                            "status": "not_found"
                        }
                        json.dump(out_data, out_file, ensure_ascii=False)
                        out_file.write("\n")
        except FileNotFoundError:
            raise GeocoderError(f"Файл не найден: {input_path}")
        except IOError as e:
            raise GeocoderError(f"Ошибка ввода-вывода при работе с файлами: {e}")

    @staticmethod
    def _normalize_score(raw_score: float, top_score: float) -> float:
        if top_score <= 0:
            return 100.0
        return min(round((raw_score / top_score) * 100, 1), 100.0)

    def _aggregate_results(self, choices: list[dict], limit: int) -> list[dict]:

        grouped: dict[tuple, dict] = {}
        top_score = choices[0].get("score", 1.0) if choices else 1.0

        for item in choices:
            key = (item["region"], item["city"], item["street"], item["house"])

            if key not in grouped:
                if len(grouped) >= limit:
                    continue  # уже набрали limit уникальных адресов

                grouped[key] = {
                    "format_address": format_address(
                        region=item["region"],
                        city=item.get("city"),
                        street=item.get("street"),
                        house=item.get("house")
                    ),
                    "region": item["region"],
                    "city": item["city"],
                    "street": item["street"],
                    "house": item["house"],
                    "orgs": [],
                    "lat": item["lat"],
                    "lon": item["lon"],
                    "similarity_score": self._normalize_score(item.get("score", 1.0), top_score),
                }

            if item.get("org") and item["org"] not in grouped[key]["orgs"]:
                grouped[key]["orgs"].append(item["org"])

        return list(grouped.values())