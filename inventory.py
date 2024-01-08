#!/usr/bin/env python3
import etcd3
import argparse
import sys
import csv
import json
import tabulate
import xml.etree.ElementTree as ET
import logging
from typing import List, Tuple, Dict, Protocol, Any
from functools import wraps

# Configuration and logging setup
CONFIG = {"etcd_host": "localhost", "etcd_port": 2379, "base_key": "/hosts/"}
logging.basicConfig(level=logging.INFO)


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
    def __init__(self):
        self.client = etcd3.client(host=CONFIG["etcd_host"], port=CONFIG["etcd_port"])

    @handle_exceptions
    def put(self, key: str, value: str):
        self.client.put(key, value)

    @handle_exceptions
    def get(self, key: str) -> Tuple[bytes, Any]:
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
    def list_hosts(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Lists all hosts in the inventory."""
        hosts = []
        for key, value in self.etcd.get_prefix(self.base_key):
            host_name = key.decode("utf-8").replace(self.base_key, "")
            host_data = json.loads(value.decode("utf-8"))
            hosts.append((host_name, host_data))
        return hosts

    @handle_exceptions
    def get_host_data(self, host_name: str) -> Dict[str, Any]:
        """Gets the data of the host with the given name."""
        key = self._build_key(host_name)
        _, value = self.etcd.get(key)
        return json.loads(value.decode("utf-8")) if value else None


class OutputFormatterFactory:
    formatters = {}

    @classmethod
    def register_formatter(cls, output_format: str, formatter_cls):
        cls.formatters[output_format] = formatter_cls

    @classmethod
    def create(cls, output_format: str, hosts: List[Tuple[str, Dict[str, Any]]]):
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


class OutputFormatterProtocol(Protocol):
    def __init__(self, hosts: List[Tuple[str, Dict[str, Any]]]):
        ...

    def output(self):
        ...


class BaseOutputFormatter(OutputFormatterProtocol):
    def __init__(self, hosts: List[Tuple[str, Dict[str, Any]]]):
        self.hosts = hosts

    def output(self):
        raise NotImplementedError("Subclasses should implement this method.")


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


def parse_host_data(host_data_str: str) -> Dict[str, Any]:
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
    parser.add_argument(
        "--etcd-host", default=CONFIG["etcd_host"], help="etcd server address"
    )
    parser.add_argument(
        "--etcd-port", type=int, default=CONFIG["etcd_port"], help="etcd server port"
    )
    parser.add_argument(
        "--output",
        choices=OutputFormatterFactory.get_available_formats(),
        default="table",
        help="Output format",
    )

    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

    create_parser = subparsers.add_parser("create", help="Create a host")
    create_parser.add_argument("host_name", help="Host name")
    create_parser.add_argument(
        "host_data", help="Host data in JSON, XML, or key-value format"
    )

    update_parser = subparsers.add_parser("update", help="Update a host field")
    update_parser.add_argument("host_name", help="Host name")
    update_parser.add_argument("field_name", help="Field name")
    update_parser.add_argument("field_value", help="Field value")

    remove_parser = subparsers.add_parser("remove", help="Remove a host")
    remove_parser.add_argument("host_name", help="Host name to remove")

    list_parser = subparsers.add_parser("list", help="List all hosts")

    args = parser.parse_args()
    inventory = HostInventory()

    if args.subcommand == "create":
        host_data = parse_host_data(args.host_data)
        inventory.create_host(args.host_name, host_data)
        logging.info("Host created successfully!")

    elif args.subcommand == "modify":
        inventory.modify_host(args.host_name, args.field_name, args.field_value)

    elif args.subcommand == "remove":
        inventory.remove_host(args.host_name)

    elif args.subcommand == "list":
        hosts = inventory.list_hosts()
        formatter = OutputFormatterFactory.create(output_format, hosts)
        if formatter:
            formatter.output()


def parse_host_data(host_data_str: str) -> Dict[str, Any]:
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


if __name__ == "__main__":
    main()
