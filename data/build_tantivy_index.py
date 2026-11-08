import time
from pathlib import Path
import tantivy
import sqlite3
def build_schema() -> tantivy.Schema:
    sb = tantivy.SchemaBuilder()
    sb.add_text_field("region", stored=True)
    sb.add_text_field("city", stored=True)
    sb.add_text_field("street", stored=True)
    sb.add_text_field("house", stored=True)
    sb.add_text_field("org", stored=True)
    sb.add_float_field("lat", stored=True)
    sb.add_float_field("lon", stored=True)
    return sb.build()


def create_or_open_index(index_path: Path) -> tantivy.Index:
    index_path = Path(index_path)
    if index_path.exists() and any(index_path.iterdir()):
        return tantivy.Index.open(str(index_path))

    index_path.mkdir(parents=True, exist_ok=True)
    schema = build_schema()
    return tantivy.Index(schema, path=str(index_path))


def index_from_sqlite(sqlite_path: Path, index_path: Path, batch_size: int = 100_000, heap_size: int = 256_000_000) -> None:
    sqlite_path = Path(sqlite_path)
    index_path = Path(index_path)


    index = create_or_open_index(index_path)
    writer = index.writer(heap_size=heap_size)

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT region, city, street, house, org, lat, lon FROM addresses")

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        for row in rows:
            writer.add_document(tantivy.Document(
                region=[row["region"] or ""],
                city=[row["city"] or ""],
                street=[row["street"] or ""],
                house=[row["house"] or ""],
                org=[row["org"] or ""],
                lat=float(row["lat"] or 0.0),
                lon=float(row["lon"] or 0.0)
            ))

    writer.commit()
    index.reload()
    conn.close()

def main():
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "geocoder.db"
    index_path = base_dir / "geocoder_tantivy"

    if not db_path.exists():
        print(f"База данных {db_path} не найдена")
        return
    
    index_from_sqlite(db_path, index_path)

if __name__ == "__main__":
    main()
