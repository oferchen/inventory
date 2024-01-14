# inventory/hostinventory.py
import json
import logging
from typing import Any, Dict, Optional, Protocol, Union

from config import Config
from etcd_client import EtcdClient
from utils import handle_exceptions


class Host:
    def __init__(self, name: str, **attributes) -> None:
        self.name = name
        self.attributes: Dict[str, str] = attributes
        logging.info(f"Host '{name}' initialized with attributes: {attributes}")

    def __json__(self):
        return {
            'attributes': self.attributes
        }

    @handle_exceptions
    def add_attribute(self, key: str, value: str) -> None:
        if not key.strip():
            raise ValueError("Attribute name must be a non-empty string")
        self.attributes[key] = value
        logging.info(f"Attribute '{key}' with value '{value}' added to host '{self.name}'")

    @handle_exceptions
    def update_attribute(self, key: str, value: str) -> None:
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

    @handle_exceptions
    def list_attributes(self) -> Dict[str, str]:
        return self.attributes.copy()

    def get_attribute(self, key: str) -> Optional[str]:
        return self.attributes.get(key)



class HostStorage(Protocol):
    def put(self, key: str, value: Dict[str, str]) -> None:
        ...

    def get(self, key: str) -> Optional[Dict[str, str]]:
        ...

    def delete(self, key: str) -> None:
        ...

    def get_all(self) -> Dict[str, Dict[str, str]]:
        ...


class HostInventory:
    def __init__(self, storage: HostStorage) -> None:
        self.storage = storage
        self.hosts: Dict[str, Dict[str, str]] = self.load_hosts()

    def load_hosts(self) -> Dict[str, Host]:
        data = self.storage.get_all()
        return {key: Host(name=key, attributes=attributes) for key, attributes in data.items()}

    @handle_exceptions
    def create_host(self, host_name: str, host_data: Dict[str, str]) -> None:
        if host_name in self.hosts:
            logging.warning(f"Host '{host_name}' already exists. Skipping creation.")
            return
        host = Host(name=host_name, **host_data)
        self.storage.put(host_name, host.list_attributes())
        self.hosts[host_name] = host
        logging.info(f"Host '{host_name}' created successfully.")

    @handle_exceptions
    def update_host(self, host_name: str, key: str, value: str) -> None:
        if host_name not in self.hosts:
            raise KeyError(f"Host '{host_name}' not found")

        host = self.hosts[host_name]
        host.update_attribute(key, value)
        self.storage.put(host_name, host.list_attributes())

    @handle_exceptions
    def remove_host(self, host_name: str) -> None:
        if host_name not in self.hosts:
            raise KeyError(f"Host '{host_name}' not found")

        self.storage.delete(host_name)
        del self.hosts[host_name]

    def list_hosts(self, filter_args: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, str]]:
        return self.hosts
