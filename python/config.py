# config.py

class Config:
    ETCD_DEFAULT_HOST = "localhost"
    ETCD_DEFAULT_PORT = 2379
    ETCD_ALLOW_RECONNECT = True
    ETCD_ATTEMPTS = 3
    ETCD_RETRY_DELAY = 2
    ETCD_HOSTS_BASE_DIR = "/hosts/"
