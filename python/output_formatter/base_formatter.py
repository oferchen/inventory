# output_formatter/base_formatter.py
from typing import Any, Dict, List, Union, Type, Protocol, Tuple


class OutputFormatterProtocol(Protocol):
    def __init__(self, hosts: List[Tuple[str, Dict[str, Any]]]) -> None:
        ...

    def output(self):
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
        cls, format_name: str, hosts: List[Union[str, Dict[str, Union[bool, float, str]]]]
    ) -> Union[OutputFormatterProtocol, None]:
        """Create an instance of an output formatter based on the format name."""
        if formatter_class := cls._formatters.get(format_name):
            return formatter_class(hosts)
        else:
            return None


class BaseOutputFormatter(OutputFormatterProtocol):
    def __init__(self, hosts: List[Tuple[str, Dict[str, Any]]]):
        self.hosts = hosts

    def output(self):
        raise NotImplementedError("Subclasses should implement this method.")
