import sqlite3
from pathlib import Path


def create_test_db():
    db_path = Path(__file__).parent / "geocoder_test.db"
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
        ('новосибирская обл', 'новосибирск', 'ленина', '5', 'сбербанк', 55.0302, 82.9204)
    ]

    cursor.executemany('''
        INSERT INTO addresses (region, city, street, house, org, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', test_data)

    conn.commit()
    conn.close()
    print(f"Тестовая база данных успешно создана {db_path}")


if __name__ == '__main__':
    create_test_db()
