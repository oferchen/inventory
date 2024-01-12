# inventory/host.py
import logging
from typing import Any, Dict, List, Optional, Tuple

from config import CONFIG
from utils.utils import handle_exceptions

class Host:
    def __init__(self, name: str) -> None:
        if not name.strip():
            logging.error("Invalid host name: must be a non-empty string")
            raise ValueError("Host name must be a non-empty string")
        self.name = name
        self.fields: Dict[str, Any] = {}
        logging.info(f"Host '{name}' initialized")

        self.name = name
        self.fields = {}
        logging.info(f"Host '{name}' initialized")

    @handle_exceptions
    def add_field(self, field_name: str, value: Any) -> None:
        if not field_name.strip():
            logging.error("Invalid field name: must be a non-empty string")
            raise ValueError("Field name must be a non-empty string")

        self.fields[field_name] = value
        logging.info(f"Field '{field_name}' added to host '{self.name}'")

    @handle_exceptions
    def update_field(self, field_name: str, value: Any) -> None:
        if field_name not in self.fields:
            logging.error(f"Attempted to update non-existing field '{field_name}' in host '{self.name}'")
            raise KeyError(f"Field '{field_name}' does not exist in host '{self.name}'")

        self.fields[field_name] = value
        logging.info(f"Field '{field_name}' updated in host '{self.name}'")


    @handle_exceptions
    def remove_field(self, field_name: str) -> None:
        if field_name not in self.fields:
            logging.error(f"Attempted to remove non-existing field '{field_name}' in host '{self.name}'")
            raise KeyError(f"Field '{field_name}' does not exist in host '{self.name}'")

        del self.fields[field_name]
        logging.info(f"Field '{field_name}' removed from host '{self.name}'")

    def get_field(self, field_name: str) -> Any:
        return self.fields.get(field_name)

    def get_all_fields(self) -> Dict[str, Any]:
        return self.fields

