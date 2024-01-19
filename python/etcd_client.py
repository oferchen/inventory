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

    def __new__(cls, etcd_host: str = None, etcd_port: int = None, etcd_allow_reconnect: bool = None, base_dir: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(EtcdClient, cls).__new__(cls)
            cls._instance.etcd_host = etcd_host or Config.ETCD_DEFAULT_HOST
            cls._instance.etcd_port = etcd_port or Config.ETCD_DEFAULT_PORT
            cls._instance.etcd_allow_reconnect = etcd_allow_reconnect or Config.ETCD_ALLOW_RECONNECT
            cls._instance.base_dir = base_dir or Config.ETCD_HOSTS_BASE_DIR
            cls._instance.client = client(host=cls._instance.etcd_host, port=cls._instance.etcd_port)
        return cls._instance

    @handle_exceptions
    def put(self, key: str, value: Any) -> bool:
        """
        Store a value in Etcd.
        Args:
            key (str): The key under which the value is stored.
            value (Any): The value to be stored.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            full_key = f"{self.base_dir}{key}"
            self.client.put(full_key, json.dumps(value))
            logging.debug(f"Successfully put data at key: {full_key}")
            return True
        except Exception as e:
            logging.error(f"Error in putting key '{key}': {e}")
            return False

    @handle_exceptions
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from Etcd.
        Args:
            key (str): The key whose value is to be retrieved.
        Returns:
            Optional[Any]: The retrieved value, or None if not found or an error occurred.
        """
        try:
            full_key = f"{self.base_dir}{key}"
            response, _ = self.client.get(full_key)
            if response:
                logging.debug(f"Retrieved data for key: {full_key}, Data: {response}")
                return json.loads(response.decode('utf-8')) if response else None
            else:
                logging.debug(f"No data found for key: {key}")
                return None
        except Exception as e:
            logging.error(f"Error in getting key '{key}': {e}")
            return None

    @handle_exceptions
    def get_all(self) -> Dict[str, Dict[str, str]]:
        """
        Retrieve all host data from Etcd.
        Returns:
        Dict[str, Dict[str, str]]: All host data indexed by host name.
        """
        all_data = {}
        try:
            logging.debug(f"Retrieving all data from Etcd {self.base_dir}")
            for value, metadata in self.client.get_prefix(self.base_dir):
                key = metadata.key.decode('utf-8').replace(self.base_dir, '')
                all_data[key] = json.loads(value.decode('utf-8')) if value else None
            logging.debug(f"Retrieved all data: {all_data}")
            return all_data
        except Exception as e:
            logging.error(f"Error getting all data: {e}")
            return all_data

    @handle_exceptions
    def delete(self, key: str) -> None:
        full_key = f"{self.base_dir}{key}"
        self.client.delete(full_key)

    @handle_exceptions
    def get_prefix(self):
        return f"{self.client.get_prefix}"
