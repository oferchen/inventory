# utils/utils.py
import logging
import sys
from functools import wraps


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
            sys.exit(e.code)
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            sys.exit(1)
    return wrapper
