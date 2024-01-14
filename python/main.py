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
    logging.basicConfig(level=logging.INFO)
    main()
