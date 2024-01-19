# utils/utils.py
import logging
from functools import wraps

# Custom Exceptions
class HostAttributeError(Exception):
    pass

class HostNotFoundError(Exception):
    pass

class CustomException(Exception):
    def __init__(self, message: str, code: int = 1):
        self.code = code
        super().__init__(message)

def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CustomException as e:
            logging.error(e)
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
    return wrapper
