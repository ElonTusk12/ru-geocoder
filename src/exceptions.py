class GeocoderError(Exception):
    """Базовый класс для всех ошибок геокодера"""
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