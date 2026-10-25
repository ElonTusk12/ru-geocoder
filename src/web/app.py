from typing import Annotated
from fastapi import FastAPI, HTTPException, Query
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from src.core.engine import GeocoderEngine
from src.exceptions import AddressNotFoundError, AddressParseError, GeocoderError

app = FastAPI(title="RU-Geocoder API")

app.mount("/static", StaticFiles(directory="static"), name="static")

engine = GeocoderEngine()
@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/api/geocode")
async def geocode(
        address: Annotated[str, Query(description="Адрес")],
        limit: Annotated[int, Query(ge=1, description="Количество вариантов")] = 1
):
    try:
        results = engine.geocode(address, number_of_addresses=limit)
        return {"status": "success", "data": results}
    except AddressNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AddressParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GeocoderError as e:
        raise HTTPException(status_code=500, detail=str(e))


