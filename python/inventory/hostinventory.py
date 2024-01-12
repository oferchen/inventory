# inventory/hostinventory.py
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

class HostInventory:
    def __init__(self) -> None:
        self.hosts: Dict[str, Host] = {}

    @handle_exceptions
    def create_host(self, host_name: str, host_data: Dict[str, Any]) -> None:
        if host_name in self.hosts:
            logging.error(f"Host '{host_name}' already exists")
            raise KeyError(f"Host '{host_name}' already exists")
        host = Host(host_name)
        for field_name, value in host_data.items():
            try:
                host.add_field(field_name, value)
            except ValueError as e:
                logging.error(f"Error in creating host '{host_name}': {e}")
        self.hosts[host_name] = host
        logging.info(f"Host '{host_name}' created successfully")

    @handle_exceptions
    def update_host(self, host_name: str, field_name: str, value: Any) -> None:
        host = self.hosts.get(host_name)
        if not host:
            logging.error(f"Host '{host_name}' not found")
            raise KeyError(f"Host '{host_name}' not found")
        try:
            host.update_field(field_name, value)
            logging.info(f"Host '{host_name}' updated successfully")
        except KeyError as e:
            logging.error(f"Error in updating host '{host_name}': {e}")

    @handle_exceptions
    def remove_host(self, host_name: str) -> None:
        if host_name not in self.hosts:
            logging.error(f"Host '{host_name}' not found")
            raise KeyError(f"Host '{host_name}' not found")
        del self.hosts[host_name]
        logging.info(f"Host '{host_name}' removed successfully")

    def get_host(self, host_name: str) -> Optional[Host]:
        return self.hosts.get(host_name)

    def list_hosts(self) -> Dict[str, Host]:
        return self.hosts
