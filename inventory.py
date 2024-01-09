#!/usr/bin/env python3
import argparse
import csv
import json
import logging
import operator
import re
import sys
import xml.etree.ElementTree as ET
from functools import annotations, wraps
from typing import List, Tuple, Dict, Protocol, Any, Union, Optional

import etcd3
import tabulate


# Define constants for configuration
ETCD_DEFAULT_HOST = "localhost"
ETCD_DEFAULT_PORT = 2379

# Configuration and logging setup
CONFIG = {
    "etcd_host": ETCD_DEFAULT_HOST,
    "etcd_port": ETCD_DEFAULT_PORT,
    "base_key": "/hosts/",
}
logging.basicConfig(level=logging.INFO)


class ExpressionFilter:
    def __init__(self, data):
        self.data = data

    def evaluate(self, specification: str) -> Union[bool, float, str]:
        # Remove double quotes around the specification
        specification = specification.strip('"')

        # Create a parser and parse the specification
        parser = Parser(specification)
        parsed_expression = parser.parse()

        # Evaluate the parsed expression
        return parsed_expression.evaluate(self.data)


class Expression:
    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        pass


class BinaryOperator(Expression):
    def __init__(self, left: Expression, right: Expression, operator_func):
        self.left = left
        self.right = right
        self.operator_func = operator_func

    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        left_result = self.left.evaluate(data)
        right_result = self.right.evaluate(data)
        return self.operator_func(left_result, right_result)


class UnaryOperator(Expression):
    def __init__(self, operand, operator_func):
        self.operand = operand
        self.operator_func = operator_func

    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        operand_result = self.operand.evaluate(data)
        return self.operator_func(operand_result)


class Field(Expression):
    def __init__(self, field_name):
        self.field_name = field_name

    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        return data.get(self.field_name)


class Value(Expression):
    def __init__(self, value: Union[bool, float, str]):
        self.value = value

    def evaluate(self, data: Dict[str, Any]) -> Union[bool, float, str]:
        return self.value


class OperatorFactory:
    operators = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "%": operator.mod,
        "&&": operator.and_,
        "||": operator.or_,
        "!": operator.not_,
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
        "=~": re.match,
        "is": operator.is_,
        "isnt": operator.is_not,
        "&": operator.and_,
        "|": operator.or_,
        "~": operator.xor,
        "^": operator.pow,
        "<<": operator.lshift,
        ">>": operator.rshift,
        ">>>": operator.rshift,
    }

    @classmethod
    def create_operator(cls, operator_symbol, left, right):
        operator_func = cls.operators.get(operator_symbol)
        if operator_func:
            return BinaryOperator(left, right, operator_func)
        raise ValueError(f"Operator {operator_symbol} not supported")


class FunctionFactory:
    functions = {
        "round": round,
        "ceiling": lambda x: int(x) if x == int(x) else int(x) + 1,
        "floor": lambda x: int(x),
        "startswith": str.startswith,
        "endswith": str.endswith,
        "glob": re.search,
        "member": lambda x, y: x in y,
        "size": len,
        "conjunction": set.intersection,
        "keys": lambda x, y, z: {item.split(z)[0] for item in x.split(y)},
        "list": lambda x, y=None: x.split(y) if y else x.split(","),
        "equals": lambda x, y: x == y,
    }

    @classmethod
    def create_function(cls, function_name: str, *args: Expression) -> UnaryOperator:
        function = cls.functions.get(function_name)
        if function:
            return UnaryOperator(args[0], function)
        raise ValueError(f"Function {function_name} not supported")


class Parser:
    def __init__(self, specification):
        self.specification = specification
        self.tokenizer = Tokenizer(specification)

    def parse(self):
        expression = self.parse_expression()
        if self.tokenizer.has_tokens():
            raise ValueError("Invalid expression")
        return expression

    def parse_expression(self, precedence=0):
        left = self.parse_operand()
        while self.tokenizer.has_tokens():
            token = self.tokenizer.peek()
            token_precedence = self.get_precedence(token)
            if token_precedence < precedence:
                return left
            self.tokenizer.next()
            right = self.parse_expression(token_precedence + 1)
            left = OperatorFactory.create_operator(token, left, right)
        return left

    def parse_operand(self) -> Expression:
        token = self.tokenizer.peek()
        if token == "(":
            self.tokenizer.next()
            expression = self.parse_expression()
            if self.tokenizer.peek() != ")":
                raise ValueError("Missing closing parenthesis")
            self.tokenizer.next()
            return expression
        elif token.startswith('"') or token.startswith("'"):
            return Value(token.strip("\"'"))
        elif token.isnumeric():
            return Value(float(token))
        elif re.match(r"^[a-zA-Z_][a-zA-Z_0-9]*$", token):
            return Field(token)
        elif token.isalnum():
            return Value(token)
        else:
            raise ValueError(f"Invalid token: {token}")

    def get_precedence(self, operator_symbol):
        precedence = {
            "&&": 1,
            "||": 1,
            "!": 2,
            "<": 3,
            "<=": 3,
            ">": 3,
            ">=": 3,
            "==": 3,
            "!=": 3,
            "=~": 3,
            "is": 3,
            "isnt": 3,
            "&": 4,
            "|": 4,
            "~": 4,
            "^": 4,
            "<<": 5,
            ">>": 5,
            ">>>": 5,
            "?": 6,
            ":": 6,
        }
        return precedence.get(operator_symbol, 0)


class Tokenizer:
    def __init__(self, specification):
        self.tokens = re.findall(
            r"\b(?:[+\-*/%]|\w+|>=?|<=?|!=|==|&&|\|\||[()])\b", specification
        )
        self.current = 0

    def peek(self) -> Optional[str]:
        if self.has_tokens():
            return self.tokens[self.current]
        return None

    def next(self):
        if self.has_tokens():
            self.current += 1

    def has_tokens(self):
        return self.current < len(self.tokens)


def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            sys.exit(1)

    return wrapper


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

    def _filter_host(
        self, host_data: Dict[str, Any], filter_specification: str
    ) -> bool:
        """Filter a host based on the filter specification.

        Args:
            host_data (Dict[str, Any]): The host data to filter.
            filter_specification (str): The filter specification.

        Returns:
            bool: True if the host matches the filter, False otherwise.
        """
        # Create an ExpressionFilter with the host data and evaluate the filter specification
        filter_evaluator = ExpressionFilter(host_data)
        return filter_evaluator.evaluate(filter_specification)

    @handle_exceptions
    def get_host_data(self, host_name: str) -> Optional[Dict[str, Any]]:
        """Gets the data of the host with the given name.

        Args:
            host_name (str): The name of the host.

        Returns:
            Optional[Dict[str, Any]]: The host data as a dictionary, or None if the host is not found.
        """
        key = self._build_key(host_name)
        _, value = self.etcd.get(key)
        return json.loads(value.decode("utf-8")) if value else None


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


class OutputFormatterFactory:
    formatters = {}

    @classmethod
    def register_formatter(cls, output_format: str, formatter_cls):
        cls.formatters[output_format] = formatter_cls

    @classmethod
    def create(
        cls, output_format: str, hosts: List[Tuple[str, Dict[str, Any]]]
    ) -> Optional[BaseOutputFormatter]:
        formatter_cls = cls.formatters.get(output_format)
        if formatter_cls:
            return formatter_cls(hosts)
        else:
            logging.error(f"No formatter registered for format: {output_format}")
            return None

    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Returns a list of available output formats."""
        return list(cls.formatters.keys())


# CSV Output Formatter
class CsvOutputFormatter(BaseOutputFormatter):
    def output(self):
        writer = csv.writer(sys.stdout)
        writer.writerow(["Host Name", "Host Data"])
        for host_name, host_data in self.hosts:
            writer.writerow([host_name, json.dumps(host_data)])
        logging.info("CSV output generated successfully.")


# JSON Output Formatter
class JsonOutputFormatter(BaseOutputFormatter):
    def output(self):
        host_dict = {host_name: host_data for host_name, host_data in self.hosts}
        print(json.dumps(host_dict, indent=4))
        logging.info("JSON output generated successfully.")


# XML Output Formatter
class XmlOutputFormatter(BaseOutputFormatter):
    def output(self):
        root = ET.Element("hosts")
        for host_name, host_data in self.hosts:
            host_element = ET.SubElement(root, "host")
            ET.SubElement(host_element, "name").text = host_name
            ET.SubElement(host_element, "data").text = json.dumps(host_data)
        xml_string = ET.tostring(root, encoding="unicode")
        print(xml_string)
        logging.info("XML output generated successfully.")


# Table Output Formatter
class TableOutputFormatter(BaseOutputFormatter):
    def output(self):
        headers = ["Host Name", "Host Data"]
        table_data = [
            (host_name, json.dumps(host_data)) for host_name, host_data in self.hosts
        ]
        print(tabulate.tabulate(table_data, headers, tablefmt="grid"))
        logging.info("Table output generated successfully.")


# Block Output Formatter
class BlockOutputFormatter(BaseOutputFormatter):
    def output(self):
        for host_name, host_data in self.hosts:
            print(f"Host: {host_name}")
            for key, value in host_data.items():
                print(f"  {key}: {value}")
            print("-" * 20)
        logging.info("Block output generated successfully.")


# RFC 4180-compliant CSV Output Formatter
class Rfc4180CsvOutputFormatter(BaseOutputFormatter):
    def output(self):
        writer = csv.writer(sys.stdout, dialect="excel")
        writer.writerow(["Host Name", "Host Data"])
        for host_name, host_data in self.hosts:
            writer.writerow([host_name, json.dumps(host_data)])
        logging.info("RFC 4180-compliant CSV output generated successfully.")


# Typed CSV Output Formatter
class TypedCsvOutputFormatter(BaseOutputFormatter):
    def output(self):
        writer = csv.writer(sys.stdout)
        writer.writerow(["Host Name", "Host Data Type", "Host Data"])
        for host_name, host_data in self.hosts:
            data_type = type(host_data).__name__
            writer.writerow([host_name, data_type, json.dumps(host_data)])
        logging.info("Typed CSV output generated successfully.")


# Script Output Formatter (CSV without header)
class ScriptOutputFormatter(BaseOutputFormatter):
    def output(self):
        writer = csv.writer(sys.stdout, quoting=csv.QUOTE_NONE)
        for host_name, host_data in self.hosts:
            writer.writerow([host_name, json.dumps(host_data)])
        logging.info("Script output generated successfully.")


def parse_host_data(host_data_str: str) -> Dict[str, Union[bool, float, str]]:
    """Detects the format of host data and parses it accordingly."""
    try:
        if host_data_str.startswith("{") and host_data_str.endswith("}"):
            return json.loads(host_data_str)
        elif "<" in host_data_str and ">" in host_data_str:
            root = ET.fromstring(host_data_str)
            return {elem.tag: elem.text for elem in root}
        else:
            return dict(item.split("=", 1) for item in host_data_str.split())
    except Exception as e:
        logging.error(f"Failed to parse host data: {str(e)}")
        sys.exit(1)


def main():
    OutputFormatterFactory.register_formatter("csv", CsvOutputFormatter)
    OutputFormatterFactory.register_formatter("json", JsonOutputFormatter)
    OutputFormatterFactory.register_formatter("xml", XmlOutputFormatter)
    OutputFormatterFactory.register_formatter("table", TableOutputFormatter)
    OutputFormatterFactory.register_formatter("block", BlockOutputFormatter)
    OutputFormatterFactory.register_formatter("rfc4180-csv", Rfc4180CsvOutputFormatter)
    OutputFormatterFactory.register_formatter("typed-csv", TypedCsvOutputFormatter)
    OutputFormatterFactory.register_formatter("script", ScriptOutputFormatter)
    parser = argparse.ArgumentParser(description="Manage a host inventory using etcd.")
    # Command-line argument for specifying etcd server
    parser.add_argument(
        "--etcd-host",
        default=ETCD_DEFAULT_HOST,
        help="etcd server address (default: localhost)",
    )
    parser.add_argument(
        "--etcd-port",
        type=int,
        default=ETCD_DEFAULT_PORT,
        help="etcd server port (default: 2379)",
    )
    parser.add_argument(
        "--output",
        choices=OutputFormatterFactory.get_available_formats(),
        default="table",
        help="Output format",
    )

    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

    def create_subparser(subparsers, command, help_text):
        subparser = subparsers.add_parser(command, help=help_text)
        return subparser

    create_parser = create_subparser(subparsers, "create", "Create a host")
    update_parser = create_subparser(subparsers, "update", "Update a host field")
    remove_parser = create_subparser(subparsers, "remove", "Remove a host")
    list_parser = create_subparser(subparsers, "list", "List all hosts")

    # Create subparser
    create_parser.add_argument("host_name", help="Host name")
    create_parser.add_argument(
        "host_data", help="Host data in JSON, XML, or key-value format"
    )

    # Update subparser
    update_parser.add_argument("host_name", help="Host name")
    update_parser.add_argument("field_name", help="Field name")
    update_parser.add_argument("field_value", help="Field value")

    # Remove subparser
    remove_parser.add_argument("host_name", help="Host name to remove")

    # List subparser
    list_parser.add_argument(
        "filter", help="Filter hosts by field name and value specification"
    )

    args = parser.parse_args()
    inventory = HostInventory()

    if args.subcommand == "create":
        host_data = parse_host_data(args.host_data)
        inventory.create_host(args.host_name, host_data)
        logging.info("Host created successfully!")

    elif args.subcommand == "update":
        inventory.update_host(args.host_name, args.field_name, args.field_value)

    elif args.subcommand == "remove":
        inventory.remove_host(args.host_name)

    elif args.subcommand == "list":
        hosts = inventory.list_hosts(args.filter)
        formatter = OutputFormatterFactory.create(args.output, hosts)
        if formatter:
            formatter.output()
    else:
        # Display custom error message and help if no subcommand is provided
        logging.error("Error: Subcommand is required.")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
