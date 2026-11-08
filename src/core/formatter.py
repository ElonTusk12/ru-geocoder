from typing import Optional


def format_address(
    region: Optional[str] = "",
    city: Optional[str] = "",
    street: Optional[str] = "",
    house: Optional[str] = "",
    org: Optional[str] = None,
) -> str:
    
    region_str = str(region or "")
    city_part = f", г. {city}" if city else ""
    street_part = f", ул. {street}" if street else ""
    house_part = f", д. {house}" if house else ""
    org_part = f"{org}, " if org else ""

    addr = f"{org_part}{region_str}{city_part}{street_part}{house_part}"
    if addr.startswith(", "):
        addr = addr[2:]
    return addr
