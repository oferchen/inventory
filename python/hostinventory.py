# inventory/hostinventory.py
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from config import CONFIG
from etcd_client import EtcdClient
from utils import handle_exceptions


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
    def __init__(self, etcd_client: EtcdClient) -> None:
        self.etcd_client = etcd_client
        self.hosts: Dict[str, Host] = {}

    @handle_exceptions
    def create_host(self, host_name: str, host_data: Dict[str, str]) -> None:
        if not host_name:
            raise ValueError("Host name cannot be empty")

        if host_name in self.hosts:
            raise KeyError(f"Host '{host_name}' already exists")

        host = Host(host_name)
        for field_name, value in host_data.items():
            if not field_name:
                raise ValueError("Field name cannot be empty")
            host.add_attribute(field_name, value)

        self.etcd_client.put(host_name, host_data)
        self.hosts[host_name] = host
        logging.info(f"Host '{host_name}' created successfully")

    @handle_exceptions
    def update_host(self, host_name: str, key: str, value: str) -> None:
        if not host_name:
            raise ValueError("Host name cannot be empty")

        host = self.hosts.get(host_name)
        if not host:
            raise KeyError(f"Host '{host_name}' not found")

        if not key:
            raise ValueError("Field name cannot be empty")

        host.update_attribute(key, value)
        self.etcd_client.put(host_name, json.dumps(host.list_attributes()))
        logging.info(f"Host '{host_name}' updated successfully")

    @handle_exceptions
    def remove_host(self, host_name: str) -> None:
        if not host_name:
            raise ValueError("Host name cannot be empty")

        if host_name not in self.hosts:
            raise KeyError(f"Host '{host_name}' not found")

        self.etcd_client.delete(host_name)
        del self.hosts[host_name]
        logging.info(f"Host '{host_name}' removed successfully")

    @handle_exceptions
    def get_host(self, host_name: str) -> Optional[Host]:
        if not host_name:
            raise ValueError("Host name cannot be empty")

        return self.hosts.get(host_name)

    @handle_exceptions
    def list_hosts(self, filter_args: Optional[Dict[str, str]] = None) -> Dict[str, Host]:
        logging.info(f"Listing hosts with filter: {filter_args}")
        full_prefix = f"{self.etcd_client.base_dir}"

        try:
            data = self.etcd_client.get_prefix(full_prefix)
            logging.info(f"Retrieved data: {data}")
        except Exception as e:
            logging.error(f"An error occurred while retrieving data from etcd: {str(e)}")
            return {}

        self.hosts.clear()

        for key, value in data:
            if isinstance(value, bytes):
                decoded_value = json.loads(value.decode('utf-8'))  # Decode JSON
            else:
                logging.warning(f"Unexpected data type for key '{key}' in etcd. Skipping.")
                continue

            decoded_key = key.decode('utf-8').replace(full_prefix, "")
            host = Host(decoded_key)
            for field_name, field_value in decoded_value.items():
                host.add_attribute(field_name, field_value)
            self.hosts[decoded_key] = host

        if filter_args:
            filtered_hosts = {}
            for host_name, host in self.hosts.items():
                if all(host.get_attribute(k) == v for k, v in filter_args.items()):
                    filtered_hosts[host_name] = host
            return filtered_hosts
        else:
            return self.hosts
