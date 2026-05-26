class GeocoderError(Exception):
    pass

class DatabaseConnectionError(GeocoderError):
    """Ошибка подключения к базе данных адресов"""
    pass

class AddressNotFoundError(GeocoderError):
    """Адрес не найден"""
    pass

class AddressParseError(GeocoderError):
    """Ошибка при парсинге строки"""
    pass