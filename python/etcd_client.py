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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EtcdClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def __init__(self, etcd_host: str, etcd_port: int, base_dir: Optional[str] = None) -> None:
        self.etcd_host = etcd_host or Config.ETCD_DEFAULT_HOST
        self.etcd_port = etcd_port or Config.ETCD_DEFAULT_PORT
        self.base_dir = base_dir or base_dir or Config.ETCD_HOSTS_BASE_DIR
        self.client = client(host=self.etcd_host, port=self.etcd_port)

    @handle_exceptions
    def put(self, key, value):
        full_key = f"{self.base_dir}{key}"
        self.client.put(full_key, json.dumps(value))

    @handle_exceptions
    def get(self, key):
        response = self.client.get(key)
        if response:
            value = response
            return json.loads(value)
        return None

    @handle_exceptions
    def delete(self, key: str) -> None:
        self.client.delete(key)

    @handle_exceptions
    def get_prefix(self, prefix):
        data = list(self.client.get_prefix(prefix))
        return data