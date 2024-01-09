# etcd_client/etcd_client.py
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import etcd3
from config import CONFIG
from utils.utils import handle_exceptions


class EtcdClient:
    def __init__(self, etcd_host=None, etcd_port=None):
        self.etcd_host = etcd_host or CONFIG["etcd_host"]
        self.etcd_port = etcd_port or CONFIG["etcd_port"]
        self.client = etcd3.client(host=self.etcd_host, port=self.etcd_port)

    @handle_exceptions
    def put(self, key: str, value: str):
        self.client.put(key, value)

    @handle_exceptions
    def get(self, key: str) -> Tuple[bytes, bytes]:
        return self.client.get(key)

    @handle_exceptions
    def delete(self, key: str):
        self.client.delete(key)

    @handle_exceptions
    def get_prefix(self, prefix: str) -> List[Tuple[bytes, bytes]]:
        return self.client.get_prefix(prefix)


class HostInventory:
    def __init__(self):
        self.etcd = EtcdClient()
        self.base_key = CONFIG["base_key"]

    def _build_key(self, host_name: str) -> str:
        """Builds a complete etcd key for a given host name."""
        return f"{self.base_key}{host_name}"

    @handle_exceptions
    def create_host(self, host_name: str, host_data: Dict[str, Any]):
        key = self._build_key(host_name)
        if not self.get_host_data(host_name):
            self.etcd.put(key, json.dumps(host_data))
            logging.info(f"Host '{host_name}' added successfully.")
        else:
            logging.error(f"Host '{host_name}' already exists.")

    @handle_exceptions
    def update_host(self, host_name: str, field_name: str, field_value: Any):
        """Updates a field of a host with the given name."""
        key = self._build_key(host_name)
        host_data = self.get_host_data(host_name)
        if host_data is not None:
            host_data[field_name] = field_value
            self.etcd.put(key, json.dumps(host_data))
            logging.info(f"Updated field '{field_name}' for host '{host_name}'.")
        else:
            logging.error(f"Host '{host_name}' not found.")

    @handle_exceptions
    def remove_host(self, host_name: str):
        """Removes the host with the given name."""
        key = self._build_key(host_name)
        self.etcd.delete(key)
        logging.info(f"Host '{host_name}' removed successfully.")

    @handle_exceptions
    def list_hosts(self, filter_specification: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Lists all hosts in the inventory that match the given filter specification.

        Args:
            filter_specification (str): The filter specification to use for filtering hosts.

        Returns:
            List[Tuple[str, Dict[str, Any]]]: A list of tuples containing host names and host data.
        """
        hosts: List[Tuple[str, Dict[str, Any]]] = []
        for key, value in self.etcd.get_prefix(self.base_key):
            host_name = key.decode("utf-8").replace(self.base_key, "")
            host_data = json.loads(value.decode("utf-8"))
            if self._filter_host(host_data, filter_specification):
                hosts.append((host_name, host_data))
        return hosts
