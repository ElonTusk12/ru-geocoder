from typing import Optional
import sqlite3
from pathlib import Path
from src.exceptions import DatabaseConnectionError, GeocoderError
from src.core.tantivy_index import search_tantivy
from src.core.formatter import format_address
from data.build_tantivy_index import create_or_open_index, index_from_sqlite

class DBClient:
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(__file__).resolve().parents[2] / "data" / "geocoder.db"

        self._conn: Optional[sqlite3.Connection] = None
        self._tantivy_index = None

    @property
    def tantivy_path(self) -> Path:
        return self.db_path.parent / (self.db_path.stem + "_tantivy")

    def _get_tantivy_index(self):
        current_index = getattr(self, "_tantivy_index", None)
        if current_index is None:
            t_path = self.tantivy_path
            if t_path.exists() and any(t_path.iterdir()):
                current_index = create_or_open_index(t_path)
                self._tantivy_index = current_index
            elif self.db_path.exists():
                try:
                    current_index = create_or_open_index(t_path)
                    index_from_sqlite(self.db_path, t_path)
                    self._tantivy_index = current_index
                except Exception:
                    self._tantivy_index = None
        return getattr(self, "_tantivy_index", None)

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

    def search_bm25(self, tokens: list[str], number_of_address: int = 1) -> list[dict]:
        """Поиск адресов через полнотекстовый индекс SQLite FTS5 с ранжированием по BM25."""
        if not tokens:
            return []

        # для случая если метод не был вызван через with
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

        try:
            cursor = self._conn.cursor()
            clauses = [f"({token} OR {token}*)" for token in tokens if token.strip()]
            fts_query = " AND ".join(clauses)

            query = """
                SELECT DISTINCT region, city, street, house, org, lat, lon,
                       bm25(addresses, 1.0, 15.0, 5.0, 2.0, 3.0) as rank
                FROM addresses
                WHERE addresses MATCH ?
                ORDER BY rank
                LIMIT ?;
            """
            cursor.execute(query, (fts_query, number_of_address))
            rows = cursor.fetchall()

            if rows:
                result_list = []
                for row in rows:
                    formatted = format_address(
                        region=row["region"],
                        city=row["city"],
                        street=row["street"],
                        house=row["house"],
                        org=row["org"]
                    )

                    result_list.append({
                        "format_address": formatted,
                        "region": row["region"],
                        "city": row["city"],
                        "street": row["street"],
                        "house": row["house"],
                        "org": row["org"],
                        "lat": row["lat"],
                        "lon": row["lon"],
                        "score": -float(row["rank"]) if "rank" in row.keys() else 1.0
                    })
                return result_list
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
            if is_local_conn and self._conn:
                self._conn.close()
                self._conn = None

    def search_addresses(self, tokens: list[str], number_of_address: int = 1) -> list[dict]:
        if not tokens:
            return []

        if not self.db_path.exists():
            raise DatabaseConnectionError(
                f"Файл базы данных не найден: {self.db_path}. Пожалуйста, запустите скрипт импорта данных: python3 data/import_data.py"
            )

        # поиск с помощью tantivy
        tantivy_idx = self._get_tantivy_index()
        if tantivy_idx is not None:
            results = search_tantivy(tantivy_idx, tokens, limit=number_of_address)
            return results

        # если индекс еще не построен
        return self.search_bm25(tokens, number_of_address=number_of_address)
