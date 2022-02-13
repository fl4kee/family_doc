class WrongDate(Exception):
    pass


class WrongCity(Exception):
    pass


class WeatherException(Exception):
    pass


def generate_error_info(msg: str) -> dict:
    return {
        "code": "400",
        "message": msg
    }
