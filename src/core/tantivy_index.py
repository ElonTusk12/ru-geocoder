import tantivy
from src.core.formatter import format_address


SCHEMA_FIELDS = {
    "region": "text",
    "city": "text",
    "street": "text",
    "house": "text",
    "org": "text",
    "lat": "float",
    "lon": "float"
}

FIELD_WEIGHTS = {
    "city": 15.0,
    "street": 5.0,
    "org": 3.0,
    "house": 2.0,
    "region": 1.0
}

FUZZY_FIELDS = {
    "city": (False, 1, True),
    "street": (False, 1, True),
    "org": (False, 1, True)
}

SEARCH_FIELDS = ["city", "street", "house", "org", "region"]


def _first(val, default=""):
    return val[0] if isinstance(val, list) and val else (val if val is not None else default)


def search_tantivy(index: tantivy.Index, tokens: list[str], limit: int = 10) -> list[dict]:
    
    if not tokens:
        return []
    
    clean_tokens = []
    for t in tokens:
        clean = "".join(ch for ch in t.lower() if ch.isalnum()).strip()
        if clean:
            clean_tokens.append(clean)
    
    if not clean_tokens:
        return []
    
    query_str = " ".join(clean_tokens)
    searcher = index.searcher()

    #четкий поиск (чисто по весам и словам)
    res = None
    try:
        query = index.parse_query(
            query_str,
            default_field_names=SEARCH_FIELDS,
            field_boosts=FIELD_WEIGHTS,
            conjunction_by_default=True
        )
        res = searcher.search(query, limit)
    except Exception:
        res = None
    
    #нечеткий поиск (если не нашлось точно, типа ошибки в написании)
    if not res or not res.hits:
        try:
            query = index.parse_query(
                query_str,
                default_field_names=SEARCH_FIELDS,
                field_boosts=FIELD_WEIGHTS,
                fuzzy_fields=FUZZY_FIELDS,
                conjunction_by_default=True
            )
            res = searcher.search(query, limit)
        except Exception:
            return []
    
    if not res or not res.hits:
        return []
    
    results = []
    for score, doc_address in res.hits:
        doc = searcher.doc(doc_address)
        raw_dict = doc.to_dict()

        fields = {k: _first(raw_dict.get(k), "") for k in ("region", "city", "street", "house", "org")}
        lat = float(_first(raw_dict.get("lat"), 0.0))
        lon = float(_first(raw_dict.get("lon"), 0.0))

        results.append({
            "format_address": format_address(**fields),
            **fields,
            "lat": lat,
            "lon": lon,
            "score": score
        })

    return results
