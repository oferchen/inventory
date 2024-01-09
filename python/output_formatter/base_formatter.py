# output_formatter/base_formatter.py
from typing import Any, Dict, List, Protocol, Tuple


class OutputFormatterProtocol(Protocol):
    def __init__(self, hosts: List[Tuple[str, Dict[str, Any]]]) -> None:
        ...

    def output(self):
        ...


class BaseOutputFormatter(OutputFormatterProtocol):
    def __init__(self, hosts: List[Tuple[str, Dict[str, Any]]]):
        self.hosts = hosts

    def output(self):
        raise NotImplementedError("Subclasses should implement this method.")
