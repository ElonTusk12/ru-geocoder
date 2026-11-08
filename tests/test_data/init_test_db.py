import sqlite3
from pathlib import Path
from src.core.tantivy_index import create_or_open_index, index_from_sqlite
import shutil


def create_test_db():
    base_dir = Path(__file__).parent
    db_path = base_dir / "geocoder_test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS addresses")

    cursor.execute(
        """
        CREATE VIRTUAL TABLE addresses USING fts5 (
            region,
            city,
            street,
            house,
            org,
            lat UNINDEXED,
            lon UNINDEXED,
            tokenize = 'unicode61 remove_diacritics 1'
        )
    """
    )

    test_data = [
        ('московская обл', 'москва', 'ленина', '15', '', 55.7558, 37.6173),
        ('ленинградская обл', 'санкт-петербург', 'невский', '20', '', 69.9666, 30.3355),
        ('новосибирская обл', 'новосибирск', 'ленина', '5', 'сбербанк', 55.0302, 82.9204),
        ('омская обл', 'омск', 'чапаева', '15', 'аптека', 55.0302, 82.9204),
        ('омская обл', 'омск', 'чапаева', '15', 'втб', 55.0302, 82.9204)
    ]

    cursor.executemany('''
        INSERT INTO addresses (region, city, street, house, org, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', test_data)

    conn.commit()
    conn.close()
    print(f"Тестовая база данных SQLite успешно создана {db_path}")

    # Создаем тестовый индекс Tantivy
    tantivy_path = base_dir / "geocoder_test_tantivy"
    if tantivy_path.exists():
        shutil.rmtree(tantivy_path)
    count = index_from_sqlite(db_path, tantivy_path)
    print(f"Тестовый индекс Tantivy успешно создан ({count} записей) в {tantivy_path}")


if __name__ == '__main__':
    create_test_db()
