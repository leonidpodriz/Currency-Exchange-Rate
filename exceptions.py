from urllib.error import URLError


class BaseSDMXException(Exception):
    restart_time: int = 60
    message: str = 'Error!'

    def get_message(self) -> str:
        return self.message % {
            'restart_time': self.restart_time,
        }


class ServiceUnavailable(BaseSDMXException, URLError):
    message = 'Service is unavailable, will try in %(restart_time)i seconds...'
