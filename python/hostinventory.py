# inventory/hostinventory.py
import json
import logging
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union

from config import Config
from etcd_client import EtcdClient
from utils import (CustomException, HostAttributeError, HostNotFoundError,
                   handle_exceptions)


class Host:
    """
    Represents a Host with a name and a set of attributes.
    """
    def __init__(self, name: str, attributes: Dict[str, Any] = None):
        if attributes is None:
            attributes = {}
        self.name = name
        self.attributes: Dict[str, Any] = attributes

    def __str__(self) -> str:
        return f"{self.name}"

    def add_attribute(self, key: str, value: Any) -> None:
        if not key.strip():
            raise ValueError("Attribute key cannot be empty")
        self.attributes[key] = value

    def get_attribute(self, key: str) -> Optional[Any]:
        return self.attributes.get(key)

    def update_attribute(self, key: str, value: Any) -> None:
        if key in self.attributes:
            self.attributes[key] = value
        else:
            raise HostAttributeError(f"Attribute '{key}' not found")

    def delete_attribute(self, key: str) -> None:
        if key in self.attributes:
            del self.attributes[key]
        else:
            raise HostAttributeError(f"Attribute '{key}' not found")


class StorageInterface(Protocol):
    def create_host(self, host: Host) -> None:
        ...
    def get_host(self, name: str) -> Optional[Host]:
        ...
    def update_host(self, name: str, host: Host) -> None:
        ...
    def delete_host(self, name: str) -> None:
        ...
    def get_all_hosts(self) -> Dict[str, Dict[str, Any]]:
        ...


class EtcdStorage:
    def __init__(self):
        self.client = EtcdClient()
        self.prefix = self.client.get_prefix()

    @handle_exceptions
    def create_host(self, host: Host) -> None:
        if not host.name.strip():
            raise ValueError("Host name cannot be empty")
        try:
            success = self.client.put(host.name, host.attributes)
            if not success:
                raise CustomException(f"Failed to create host '{host.name}' in Etcd")
        except Exception as e:
            logging.error(f"Error creating host: {e}")
            raise e

    @handle_exceptions
    def get_host(self, name: str) -> Optional[Host]:
        attributes, _ = self.client.get(name)
        return None if attributes is None else Host(name, attributes)

    @handle_exceptions
    def update_host(self, name: str, new_attributes: Dict[str, Any]) -> None:
        host = self.get_host(name)
        if host is None:
            raise HostNotFoundError(f"Host '{name}' not found in inventory")

        try:
            for key, value in new_attributes.items():
                host.update_attribute(key, value)
            self.client.put(name, host.attributes)
        except Exception as e:
            logging.error(f"Error updating host '{name}': {e}")
            raise e

    @handle_exceptions
    def delete_host(self, name: str) -> None:
        try:
            if self.get_host(name):
                self.client.delete(name)
        except Exception as e:
            logging.error(f"Error deleting host '{name}': {e}")
            raise e

    @handle_exceptions
    def get_all_hosts(self):
        try:
            all_data = self.client.get_all()
            logging.debug(f"EtcdStorage::get_all_hosts {all_data}")
            if all_data is None:
                logging.error("EtcdStorage::get_all_hosts No data returned from Etcd")
                return all_data

            logging.debug(f"EtcdStorage::get_all_hosts Retrieved all hosts data: {all_data}")
            hosts = {}
            for key, value in all_data.items():
                if value is not None:
                    logging.debug(f"EtcdStorage::get_all_hosts Key type: {type(key)}, Base dir type: {type(self.prefix)}")
                    host_name = key.replace(self.prefix, '')
                    hosts[host_name] = value
                else:
                    logging.debug(f"EtcdStorage::get_all_hosts No data found for host '{key}'")

            return hosts
        except Exception as e:
            logging.error(f"EtcdStorage::get_all_hosts Error in get_all_hosts: {e}")
            return {}

class HostInventory(StorageInterface):
    """
    Manages the inventory of hosts using a specified storage backend.
    """
    _instance = None

    def __new__(cls, filter=None, storage_backend: StorageInterface = EtcdStorage()):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.storage = storage_backend
        return cls._instance

    @handle_exceptions
    def create_host(self, host: Host) -> None:
        self.storage.create_host(host)

    @handle_exceptions
    def get_host(self, name: str) -> Optional[Host]:
        return self.storage.get_host(name)

    @handle_exceptions
    def update_host(self, name: str, host: Host) -> None:
        if not self.get_host(name):
            raise HostNotFoundError(f"Host '{name}' does not exist")
        self.storage.update_host(name, host)

    @handle_exceptions
    def delete_host(self, name: str) -> None:
        self.storage.delete_host(name)

    # @handle_exceptions
    # def list_hosts(self, filter=None) -> Dict[str, Dict[str, Any]]:
    #     all_hosts = self.storage.get_all_hosts()
    #     logging.debug(f"Hosts in Inventory: {all_hosts}")

    # #     if filter:
    # #         filter_key, filter_value = filter.split("=")
    # #         logging.debug(f"Filter Key: {filter_key}, Filter Value: {filter_value}")
    # #         filtered_hosts = {
    # #             host_name: attributes for host_name, attributes in all_hosts.items()
    # #             if attributes.get(filter_key) == filter_value
    # #         }
    # #         logging.debug(f"Filtered Hosts: {filtered_hosts}")
    # #         all_hosts = filtered_hosts

    #     return all_hosts
    @handle_exceptions
    def get_all_hosts(self) -> Dict[str, Dict[str, Any]]:
        logging.debug(f"HostInventory::get_all_hosts {self}")
        return self.storage.get_all_hosts()

class HostFactory:
    """
    Factory for creating Host objects from a string of attributes.
    """
    @staticmethod
    def create_host(name: str, attributes_str: str) -> Host:
        attributes = {}
        if attributes_str:
            for attr_pair in attributes_str.split(','):
                if '=' not in attr_pair:
                    raise ValueError("Invalid attribute format")
                key, value = attr_pair.split('=', 1)
                if key.strip() and value.strip():
                    attributes[key] = value
                else:
                    raise ValueError("Invalid attribute format")
        return Host(name, attributes)
