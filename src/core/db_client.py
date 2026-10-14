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

    def search_addresses(self, tokens: list[str], number_of_address : int = 1) -> list[dict] | None:
        if not tokens:
            return None

        #для случая если метод не был вызван через with
        is_local_conn = False
        if self._conn is None:
            try:
                self._conn = sqlite3.connect(self.db_path)
                self._conn.row_factory = sqlite3.Row
                is_local_conn = True
            except sqlite3.Error as e:
                raise DatabaseConnectionError(f"Не удалось подключиться к базе данных {self.db_path}: {e}")

        cursor = self._conn.cursor()
        fts_query = " AND ".join([f"{token}*" for token in tokens])

        query = f"""
                    SELECT region, city, street, house, lat, lon 
                    FROM addresses 
                    WHERE addresses MATCH ? 
                    LIMIT {number_of_address};
                """

        try:
            cursor.execute(query, (fts_query,))  # запрос к базе данных с параметрами
            rows = cursor.fetchall()  # извлекаем следующую строку результата запроса

            if rows:
                find_addresses = [{
                    "format_address": f"{row['region']}, г. {row['city']}, ул. {row['street']}, д. {row['house']}",
                    "region": row["region"],
                    "city": row["city"],
                    "street": row["street"],
                    "house": row["house"],
                    "lat": row["lat"],
                    "lon": row["lon"]
                }
                    for row in rows
                ]
                return find_addresses
            return None

        except sqlite3.Error as e:
            raise GeocoderError(f"Ошибка при выполнении запроса к базе данных: {e}")

        finally:
            if is_local_conn:
                if self._conn:
                    self._conn.close()
                self._conn = None






