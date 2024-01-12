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

