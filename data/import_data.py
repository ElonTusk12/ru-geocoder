import geopandas as gpd
import sqlite3
import osmium
from pathlib import Path


def regions_optimize():
    input_path = "russia_regions.geojson"
    output_path = "regions_optimized.geojson"

    #EPSG:4326 для работы с широтой/долготой
    gdf = gpd.read_file(input_path).to_crs(epsg=4326)

    #так как данные взяты из overpass turbo, то структура может быть разной
    if 'name' in gdf.columns:
        gdf['name_region'] = gdf['name'].str.strip()
    elif 'tags' in gdf.columns:
        # если только теги, то пытаемся достать имя региона из тегов
        gdf['name_region'] = gdf['tags'].apply(lambda x: x.get('name', '').strip() if isinstance(x, dict) else '')
    else:
        #ищем имя в колонках
        name_col = [c for c in gdf.columns if 'name' in c.lower()]
        if name_col:
            gdf['name_region'] = gdf[name_col[0]].str.strip()
        else:
            print("Имя найти не удалось")

    #notna - проверка на none
    gdf_optimized = gdf[['name_region', 'geometry']].copy()
    gdf_optimized = gdf_optimized[(gdf_optimized['name_region'].notna()) &
                    (gdf_optimized['name_region'] != '')]

    # preserve_topology=True не дает полигонам разрываться, simplify - упрощает границы (0.01 - километр)
    gdf_optimized['geometry'] = gdf_optimized['geometry'].simplify(tolerance=0.01, preserve_topology=True)

    gdf_optimized.to_file(output_path, driver="GeoJSON")
    print(f"Оптимизированный файл: {output_path}")


def get_any_value_or_default(some_dict : dict[str, str], keys : list[str], default) -> str:
    return next((some_dict[k] for k in keys if k in some_dict), default)

class AddressHandler(osmium.SimpleHandler):
    def __init__(self, db_cursor, conn, admin_units, buffer_size=50000):
        super().__init__()
        self.buffer = []
        self.conn = conn
        self.cursor = db_cursor
        self.buffer_size = buffer_size
        self.total_count = 0
        self.admin_units = admin_units


    def node(self, n):
        if 'addr:housenumber' in n.tags and 'addr:street' in n.tags:
            self._process_element(n, is_node=True)


    def way(self, w):
        if 'addr:housenumber' in w.tags and 'addr:street' in w.tags:
            self._process_element(w, is_node=False)
   

    def _process_element(self, element, is_node):
        region = get_any_value_or_default(element.tags, ['addr:region', 'addr:state'], '')
        
        city = get_any_value_or_default(
            element.tags,
            ['addr:city', 'addr:town', 'addr:village', 'addr:hamlet', 'addr:place', 'addr:settlement'],
            ''
        )
        
        street = get_any_value_or_default(element.tags, ['addr:street'], '')
        
        house = get_any_value_or_default(element.tags, ['addr:housenumber'], '')
        
        org = get_any_value_or_default(element.tags,
                                       ['name',
                                        'brand',
                                        'operator',
                                        'amenity',
                                        'shop',
                                        'office'], '')
        try:
            if is_node:
                lat, lon = element.location.lat, element.location.lon
            else:
                lat, lon = element.nodes[0].location.lat, element.nodes[0].location.lon
                #если нужна первая точка контура
            self.buffer.append(
                {
                    "region": region.lower().strip(),
                    "city": city.lower().strip(),
                    "street": street.lower().strip(),
                    "house": house.lower().strip(),
                    "org": org.lower().strip(),
                    "lat": lat,
                    "lon": lon,
                }
            )

            if len(self.buffer) >= self.buffer_size:
                self.commit_buffer()

        except(osmium.InvalidLocationError, IndexError):
            pass

    def commit_buffer(self):
        if not self.buffer:
            return

        df = gpd.pd.DataFrame(self.buffer) #датафрейм с колонкой geometry
        geometry = gpd.points_from_xy(df['lon'], df['lat'])
        gdf_points = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        missing_mask = (gdf_points['region'] == '') | (gdf_points['city'] == '')
        gdf_missing_admin_units = gdf_points[missing_mask].copy()
        gdf_admin_units = gdf_points[~missing_mask].copy()

        if not gdf_missing_admin_units.empty:
            # sjoin - сопоставляет точки с полигонами регионов,
            # how='left' - сохраняем все точки,
            # predicate='within' - точка внутри полигона
            joined = gpd.sjoin(gdf_missing_admin_units, self.admin_units, how='left', predicate='within')

            if 'name_region' in joined.columns:
                reg_mask = (joined['region'] == '') & (joined['name_region'].notna())
                joined.loc[reg_mask, 'region'] = joined.loc[reg_mask, 'name_region'].str.lower()

            for city_col in ['city', 'name_city', 'place_name']:
                if city_col in joined.columns:
                    city_mask = (joined['city'] == '') & (joined[city_col].notna())
                    joined.loc[city_mask, 'city'] = joined.loc[city_mask, city_col].str.lower()
                    break
            # объединяем обработанные строки и строки, где регион/город уже был
            # берем только те колонки, которые есть gdf_points
            
            empty_city_mask = (joined['city'] == '') | (joined['city'].isna())
            if empty_city_mask.any():
                joined.loc[empty_city_mask, 'city'] = ''
            

            gdf_final = gpd.GeoDataFrame(
                gpd.pd.concat([gdf_admin_units, joined[gdf_points.columns]], ignore_index=True)
            )
        else:
            gdf_final = gdf_points

        empty_final_city_mask = (gdf_final['city'] == '') | (gdf_final['city'].isna())
        if empty_final_city_mask.any():
            gdf_final.loc[empty_final_city_mask, 'city'] = ''

        gdf_final = gdf_final.drop_duplicates(subset=['region', 'city', 'street', 'house', 'lat', 'lon'])

        data_to_insert = [
            (
                row["region"],
                row["city"],
                row["street"],
                row["house"],
                row["org"],
                row["lat"],
                row["lon"],
            )
            for _, row in gdf_final.iterrows()
        ]

        self.cursor.executemany("""
            INSERT INTO addresses (region, city, street, house, org, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, data_to_insert)

        self.conn.commit()
        self.total_count += len(self.buffer)
        print(f"Импортировано адресов: {self.total_count}")
        self.buffer = []


def main():

    if not Path("regions_optimized.geojson").exists():
        regions_optimize()

    pbf_path = "ru_data_osm.pbf"
    db_path = "geocoder.db"
    regions_path = "regions_optimized.geojson"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    gdf_regions = gpd.read_file(regions_path).to_crs("EPSG:4326")
    gdf_regions["name_region"] = (
        gdf_regions["name_region"].str.lower().str.strip()
    )

    cursor.execute("DROP TABLE IF EXISTS addresses;")

    cursor.execute("""
            CREATE VIRTUAL TABLE addresses USING fts5(
                region,
                city,
                street,
                house,
                org,
                lat UNINDEXED, 
                lon UNINDEXED,
                tokenize = 'unicode61 remove_diacritics 1'
            );
        """)
    # нет смысла индексировать широту и долготу,
    # занимает большое количество места
    # и замедляет работу базы
    # tokenize = 'unicode61' - токенизатор, понимает русские символы
    # игнорирует регистр
    # remove_diacritics 1 - удаление ударений, ё
    conn.commit()

    handler = AddressHandler(cursor, conn, gdf_regions)
    handler.apply_file(pbf_path, locations=True)

    handler.commit_buffer()

    conn.close()
    print(f"\nГОТОВО! ОБЩЕЕ КОЛИЧЕСТВО ЗАПИСЕЙ: {handler.total_count}")

if __name__ == "__main__":
    main()


