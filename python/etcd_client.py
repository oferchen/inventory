# etcd_client/etcd_client.py
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from config import Config
from etcd3 import client
from utils import handle_exceptions


class EtcdClient:
    """
    Initialize the EtcdClient.
    Args:
        etcd_host (str): Etcd server address.
        etcd_port (int): Etcd server port.
        base_dir (Optional[str]): Base directory for host data in Etcd (default: None).
    """
    _instance = None

    def __new__(cls, etcd_host: str = None, etcd_port: int = None, base_dir: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(EtcdClient, cls).__new__(cls)
            cls._instance.etcd_host = etcd_host or Config.ETCD_DEFAULT_HOST
            cls._instance.etcd_port = etcd_port or Config.ETCD_DEFAULT_PORT
            cls._instance.base_dir = base_dir or Config.ETCD_HOSTS_BASE_DIR
            cls._instance.client = client(host=cls._instance.etcd_host, port=cls._instance.etcd_port)
        return cls._instance

    @handle_exceptions
    def put(self, key, value):
        full_key = f"{self.base_dir}{key}"
        self.client.put(full_key, json.dumps(value))

    @handle_exceptions
    def get(self, key):
        if response := self.client.get(key):
            value = response
            return json.loads(value)
        return None

    @handle_exceptions
    def get_all(self) -> Dict[str, Dict[str, str]]:
        """
        Retrieve all host data from Etcd.
        Returns:
        Dict[str, Dict[str, str]]: All host data indexed by host name.
        """
        all_data = {}
        for value, metadata in self.client.get_prefix(self.base_dir):
            # Correctly accessing the key from metadata
            key = metadata.key.decode('utf-8').replace(self.base_dir, '')
            all_data[key] = json.loads(value.decode('utf-8'))
        return all_data

    @handle_exceptions
    def delete(self, key: str) -> None:
        self.client.delete(key)

    @handle_exceptions
    def get_prefix(self, prefix):
        return list(self.client.get_prefix(prefix))