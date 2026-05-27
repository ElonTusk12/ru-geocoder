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

    def search_address(self, tokens: list[str]) -> dict | None:
        if not tokens:
            return None

        if not self._conn:
            raise DatabaseConnectionError("База данных не подключена. Используйте 'with'.")


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
        #lat lon - широта, долгота
        query = f"SELECT region, city, street, house, lat, lon FROM addresses WHERE " #*

        conditions = []
        params = []
        for token in tokens:

            conditions.append("(region || ' ' || city || ' ' || street || ' ' || house) LIKE ?")
            #%...% - для поиска совпадений в sql
            params.append(f"%{token}%")

        query += " AND ".join(conditions) #собираем запрос

        try:
            cursor.execute(query, params) #запрос к базе данных с параметрами
            row = cursor.fetchone() #извлекаем следующую строку результата запроса

            if row:
                format_address = f"{row['region'].title()}, г. {row['city'].title()}, ул. {row['street'].title()}, д. {row['house']}"
                return {
                    "format_address": format_address,
                    "lat": row["lat"],
                    "lon": row["lon"]
                }
            return None

        except sqlite3.Error as e:
            raise GeocoderError(f"Ошибка при выполнении запроса к базе данных: {e}")

        finally:
            if is_local_conn:
                self._conn.close()






