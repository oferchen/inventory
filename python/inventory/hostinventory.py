# inventory/hostinventory.py
import logging
from typing import Any, Dict, List, Optional, Tuple

from config import CONFIG
from utils.utils import handle_exceptions


class Host:
    def __init__(self, name: str) -> None:
        self.name = name
        self.attributes: Dict[str, str] = {}
        logging.info(f"Host '{name}' initialized")

    @handle_exceptions
    def add_attribute(self, key: str, value: str) -> None:
        if not key.strip():
            raise ValueError("Attribute name must be a non-empty string")
        self.attributes[key] = value
        logging.info(f"Attribute '{key}' with value '{value}' added to host '{self.name}'")

    @handle_exceptions
    def update_attribute(self, key: str, value: Any) -> None:
        if key not in self.attributes:
            raise KeyError(f"Attribute '{key}' not found for host '{self.name}'")
        self.attributes[key] = value
        logging.info(f"Attribute '{key}' updated for host '{self.name}'")

    @handle_exceptions
    def remove_attribute(self, key: str) -> None:
        if key not in self.attributes:
            raise KeyError(f"Attribute '{key}' not found for host '{self.name}'")
        del self.attributes[key]
        logging.info(f"Attribute '{key}' removed from host '{self.name}'")

    def get_attribute(self, key: str) -> Optional[str]:
        return self.attributes.get(key)

    def list_attributes(self) -> Dict[str, str]:
        return self.attributes.copy()

class HostInventory:
    def __init__(self) -> None:
        self.hosts: Dict[str, Host] = {}

    @handle_exceptions
    def create_host(self, host_name: str, host_data: Dict[str, Any]) -> None:
        if host_name in self.hosts:
            raise KeyError(f"Host '{host_name}' already exists")
        host = Host(host_name)
        for field_name, value in host_data.items():
            try:
                host.add_attribute(field_name, value)
            except ValueError as e:
                logging.error(f"Error in creating host '{host_name}': {e}")
                raise

        self.hosts[host_name] = host
        logging.info(f"Host '{host_name}' created successfully")

    @handle_exceptions
    def update_host(self, host_name: str, key: str, value: Any) -> None:
        host = self.hosts.get(host_name)
        if not host:
            raise KeyError(f"Host '{host_name}' not found")
        try:
            host.update_attribute(key, value)
            logging.info(f"Host '{host_name}' updated successfully")
        except (KeyError, ValueError) as e:
            logging.error(f"Error in updating host '{host_name}': {e}")
            raise

    @handle_exceptions
    def remove_host(self, host_name: str) -> None:
        if host_name not in self.hosts:
            raise KeyError(f"Host '{host_name}' not found")
        del self.hosts[host_name]
        logging.info(f"Host '{host_name}' removed successfully")

    def get_host(self, host_name: str) -> Optional[Host]:
        return self.hosts.get(host_name)

    def list_hosts(self, filter_args: Optional[Dict[str, str]] = None) -> Dict[str, Host]:
        if not filter_args:
            return self.hosts
        filtered_hosts = {}
        for host_name, host in self.hosts.items():
            match = all(
                host.get_attribute(key) == value for key, value in filter_args.items()
            )
            if match:
                filtered_hosts[host_name] = host
        return filtered_hosts
