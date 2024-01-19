# output_formatter/base_formatter.py
from typing import Any, Dict, List, Protocol, Type, Optional
from hostinventory import HostInventory, Host


class OutputFormatterProtocol(Protocol):
    def __init__(self) -> None:
        ...

    def output(self) -> None:
        ...

class OutputFormatterFactory:
    _formatters: Dict[str, Type[OutputFormatterProtocol]] = {}

    @classmethod
    def register_formatter(cls, name: str, formatter_class: Type[OutputFormatterProtocol]):
        """Register a new formatter class."""
        cls._formatters[name] = formatter_class

    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get a list of available output formats."""
        return list(cls._formatters.keys())

    @classmethod
    def create(
        cls, format_name: str, hosts: HostInventory
    ) -> Optional[OutputFormatterProtocol]:
        """Create an instance of an output formatter based on the format name."""
        if formatter_class := cls._formatters.get(format_name):
            return formatter_class(hosts)
        else:
            raise ValueError(f"Formatter '{format_name}' not found.")


class BaseOutputFormatter(OutputFormatterProtocol):
    def __init__(self, hosts: HostInventory):
        self.hosts = hosts

    def format_data(self) -> str:
        """Format the output in a specific way. To be implemented by subclasses."""
        raise NotImplementedError



