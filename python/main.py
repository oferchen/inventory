#!/usr/bin/env python3
# main.py
import argparse
import json
import logging
import sys
import xml.etree.ElementTree as ET
from typing import Dict, Union

from config import ETCD_DEFAULT_HOST, ETCD_DEFAULT_PORT
from etcd_client.etcd_client import EtcdClient
from inventory.hostinventory import Host, HostInventory
from output_formatter.base_formatter import OutputFormatterFactory
from output_formatter.formatters import (BlockOutputFormatter,
                                         CsvOutputFormatter,
                                         JsonOutputFormatter,
                                         Rfc4180CsvOutputFormatter,
                                         ScriptOutputFormatter,
                                         TableOutputFormatter,
                                         TypedCsvOutputFormatter,
                                         XmlOutputFormatter)


def parse_json(data: str) -> Dict[str, Union[bool, float, str]]:
    """
    Parse host data in JSON format.

    Args:
        data (str): Host data in JSON format.

    Returns:
        Dict[str, Union[bool, float, str]]: Parsed data as a dictionary.
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {}

def parse_xml(data: str) -> Dict[str, Union[bool, float, str]]:
    """
    Parse host data in XML format.

    Args:
        data (str): Host data in XML format.

    Returns:
        Dict[str, Union[bool, float, str]]: Parsed data as a dictionary.
    """
    try:
        root = ET.fromstring(data)
        return {elem.tag: elem.text for elem in root}
    except ET.ParseError:
        return {}

def parse_key_value(data: str) -> Dict[str, Union[bool, float, str]]:
    """
    Parse host data in key-value format.

    Args:
        data (str): Host data in key-value format (e.g., key1=value1 key2=value2).

    Returns:
        Dict[str, Union[bool, float, str]]: Parsed data as a dictionary.
    """
    return dict(item.split("=", 1) for item in data.split())

def parse_host_data(host_data_str: str) -> Dict[str, Union[bool, float, str]]:
    """
    Parse host data based on the detected format (JSON, XML, or key-value).

    Args:
        host_data_str (str): Host data in one of the supported formats.

    Returns:
        Dict[str, Union[bool, float, str]]: Parsed data as a dictionary.
    """
    parsers = [parse_json, parse_xml, parse_key_value]

    for parser in parsers:
        if parsed_data := parser(host_data_str):
            return parsed_data

    logging.error("Failed to parse host data: Invalid format")
    return {}


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
    create_parser.add_argument("key", help="Host name is considered the key")
    create_parser.add_argument(
        "host_data", help="Host data in JSON, XML, or key-value format"
    )

    # Update subparser
    update_parser.add_argument("key", help="Host name is considered the key")
    update_parser.add_argument("field_name", help="Field name")
    update_parser.add_argument("field_value", help="Field value")

    # Remove subparser
    remove_parser.add_argument("key", help="Host name is considered the key")

    # List subparser
    list_parser.add_argument(
        "filter",
        nargs="?",
        help="Filter hosts by field name and value specification (e.g., key=value)",
        default=None,
    )

    args = parser.parse_args()
    inventory = HostInventory()

    if args.subcommand == "create":
        host_data = parse_host_data(args.host_data)
        inventory.create_host(args.key, host_data)
        logging.info("Host created successfully!")

    elif args.subcommand == "update":
        inventory.update_host(args.key, args.field_name, args.field_value)

    elif args.subcommand == "remove":
        inventory.remove_host(args.key)

    elif args.subcommand == "list":
        filter_value = args.filter or None
        hosts = inventory.list_hosts(filter_value)
        formatter = OutputFormatterFactory.create(args.output, hosts)
        if formatter:
            formatter.output()
    else:
        logging.error("Error: Subcommand is required.")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
