# etcd_client/etcd_client.py
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from config import CONFIG
from etcd3 import client
from utils import handle_exceptions


class EtcdClient:
    def __init__(self, etcd_host: str, etcd_port: int, base_dir: str = None) -> None:
        self.etcd_host = etcd_host or CONFIG["etcd_host"]
        self.etcd_port = etcd_port or CONFIG["etcd_port"]
        self.base_dir = base_dir or CONFIG["base_key"]
        self.client = client(host=self.etcd_host, port=self.etcd_port)

    @handle_exceptions
    def put(self, key: str, value: str) -> None:
        full_key = f"{self.base_dir}{key}"
        self.client.put(full_key, json.dumps(value))

    @handle_exceptions
    def get(self, key: str) -> Optional[Dict[str, Union[bool, float, str]]]:
        response = self.client.get(key)
        if response:
            _, value = response
            return json.loads(value.decode('utf-8'))  # Decode JSON
        return None

    @handle_exceptions
    def delete(self, key: str) -> None:
        self.client.delete(key)

    @handle_exceptions
    def get_prefix(self, prefix: str) -> List[Tuple[bytes, bytes]]:
        logging.info(f"Retrieving data with prefix '{prefix}' from etcd")
        try:
            data = list(self.client.get_prefix(prefix.encode('utf-8')))
            logging.info(f"Retrieved data: {data}")
        except Exception as e:
            logging.error(f"An error occurred while retrieving data from etcd: {str(e)}")
            return []

        return data