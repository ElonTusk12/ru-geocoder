import sqlite3


def create_mock_db():

    conn = sqlite3.connect('data/geocoder_test.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            city TEXT,
            street TEXT,
            house TEXT,
            lat REAL,
            lon REAL
        )
    ''')

    cursor.execute('DELETE FROM addresses')

    test_data = [
        ('московская обл', 'москва', 'ленина', '15', 55.7558, 37.6173),
        ('ленинградская обл', 'санкт-петербург', 'невский', '20', 69.9666, 30.3355),
        ('новосибирская обл', 'новосибирск', 'ленина', '5', 55.0302, 82.9204)
    ]

    cursor.executemany('''
        INSERT INTO addresses (region, city, street, house, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', test_data)

    conn.commit()
    conn.close()
    print("Тестовая база данных успешно создана data/geocoder_test.db")


if __name__ == '__main__':
    create_mock_db()