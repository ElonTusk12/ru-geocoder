from typing import Optional
import sqlite3
from src.exceptions import DatabaseConnectionError, GeocoderError
from pathlib import Path

class DBClient:
    def __init__(self, db_path: Optional[str] = None):

        if db_path:
            self.db_path = Path(db_path)
        else:
            #resolve - абсолютный путь
            self.db_path = Path(__file__).resolve().parents[2] / "data" / "geocoder.db"

        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self):
        """для оператора with (открывает соединение)"""
        if not self.db_path.exists():
            raise DatabaseConnectionError(
                f"Файл базы данных не найден: {self.db_path}. Пожалуйста, запустите скрипт импорта данных: python3 data/import_data.py"
            )
        try:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            return self
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Не удалось подключиться к базе данных {self.db_path}: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.close()
            self._conn = None

    def search_addresses(self, tokens: list[str], number_of_address : int = 1) -> list[dict]:
        if not tokens:
            return []

        #для случая если метод не был вызван через with
        is_local_conn = False
        if self._conn is None:
            if not self.db_path.exists():
                raise DatabaseConnectionError(
                    f"Файл базы данных не найден: {self.db_path}. Пожалуйста, запустите скрипт импорта данных: python3 data/import_data.py"
                )
            try:
                self._conn = sqlite3.connect(self.db_path)
                self._conn.row_factory = sqlite3.Row
                is_local_conn = True
            except sqlite3.Error as e:
                raise DatabaseConnectionError(f"Не удалось подключиться к базе данных {self.db_path}: {e}")

        cursor = self._conn.cursor()
        fts_query = " AND ".join([f"{token}*" for token in tokens])
        query = f"""
                    SELECT DISTINCT region, city, street, house, org, lat, lon 
                    FROM addresses 
                    WHERE addresses MATCH ? 
                    LIMIT ?;
                """

        try:
            cursor.execute(query, (fts_query, number_of_address))  # запрос к базе данных с параметрами
            rows = cursor.fetchall()  # извлекаем следующую строку результата запроса

            if rows:
                find_addresses = [{
                    "format_address": f"{row['org'] + ', ' if row['org'] else ''}{row['region']}, г. {row['city']}, ул. {row['street']}, д. {row['house']}",
                    "region": row["region"],
                    "city": row["city"],
                    "street": row["street"],
                    "house": row["house"],
                    "org": row["org"],
                    "lat": row["lat"],
                    "lon": row["lon"]
                }
                    for row in rows
                ]
                return find_addresses
            return []

        except sqlite3.OperationalError as e:
            if "no such table: addresses" in str(e):
                raise DatabaseConnectionError(
                    f"Таблица 'addresses' не найдена в базе данных {self.db_path}. Пожалуйста, запустите скрипт импорта данных: python3 data/import_data.py"
                )
            raise GeocoderError(f"Ошибка при выполнении запроса к базе данных: {e}")
        except sqlite3.Error as e:
            raise GeocoderError(f"Ошибка при выполнении запроса к базе данных: {e}")

        finally:
            if is_local_conn:
                if self._conn:
                    self._conn.close()
                self._conn = None






