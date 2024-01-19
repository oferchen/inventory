#!/usr/bin/env python3
# main.py
import argparse
import json
import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict

from config import Config
from etcd_client import EtcdClient
from hostinventory import (EtcdStorage, HostFactory, HostInventory,
                           StorageInterface)
from output_formatter.base_formatter import OutputFormatterFactory
from output_formatter.formatters import (BlockOutputFormatter,
                                         CsvOutputFormatter,
                                         JsonOutputFormatter,
                                         Rfc4180CsvOutputFormatter,
                                         ScriptOutputFormatter,
                                         TableOutputFormatter,
                                         TypedCsvOutputFormatter,
                                         XmlOutputFormatter)


class HostDataParser:
    @staticmethod
    def parse_json(data: str) -> Dict[str, Any]:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def parse_xml(data: str) -> Dict[str, Any]:
        try:
            root = ET.fromstring(data)
            return {elem.tag: elem.text for elem in root}
        except ET.ParseError:
            return {}

    @staticmethod
    def parse_key_value(data: str) -> Dict[str, Any]:
        return dict(item.split("=", 1) for item in data.split())

    @staticmethod
    def parse_host_data(host_data_str: str) -> Dict[str, Any]:
        parsers = [HostDataParser.parse_json, HostDataParser.parse_xml, HostDataParser.parse_key_value]

        for parser in parsers:
            if parsed_data := parser(host_data_str):
                return parsed_data

        logging.error("Failed to parse host data: Invalid format")
        return {}

class HostManager:
    def __init__(self, inventory: HostInventory):
        self.inventory = inventory

    def create_host(self, name: str, host_data: Dict[str, Any]) -> None:
        host = HostFactory.create_host(name, host_data)
        self.inventory.create_host(host)
        logging.info("Host created successfully!")

    def update_host(self, name: str, field_name: str, field_value: Any) -> None:
        if host := self.inventory.get_host(name):
            host.update_attribute(field_name, field_value)
            self.inventory.update_host(name, host)
        else:
            logging.error(f"Host '{name}' not found")

    def list_hosts(self, filter: str, output_format: str):
        try:
            print("HostManager::HostInventory::get_all_hosts")
            all_hosts = self.inventory.get_all_hosts()
            print(f"Received all hosts: {all_hosts}")
            if not all_hosts:
                logging.error("No hosts found in storage")
                print({"formatted_data": "{}"})
                return
            formatted_hosts = dict(all_hosts.items())


            if filter:
                filter_key, filter_value = filter.split("=")
                formatted_hosts = {
                    name: attributes for name, attributes in formatted_hosts.items()
                    if attributes.get(filter_key) == filter_value
                }

            logging.debug(f"Hosts to be formatted: {formatted_hosts}")
            if formatter := OutputFormatterFactory.create(output_format, formatted_hosts):
                return formatter.format_data()
            logging.error(f"Unsupported output format: {output_format}")
            return None
        except Exception as e:
            logging.error(f"Error in list_hosts: {e}")


    def remove_host(self, name: str) -> None:
        self.inventory.delete_host(name)

def determine_logging_level(verbosity: int) -> int:
    if verbosity == 1:
        return logging.INFO
    elif verbosity == 2:
        return logging.DEBUG
    elif verbosity >= 3:
        return logging.NOTSET
    else:
        return logging.WARNING

def main():
    OutputFormatterFactory.register_formatter("csv", CsvOutputFormatter)
    OutputFormatterFactory.register_formatter("json", JsonOutputFormatter)
    OutputFormatterFactory.register_formatter("xml", XmlOutputFormatter)
    OutputFormatterFactory.register_formatter("table", TableOutputFormatter)
    OutputFormatterFactory.register_formatter("block", BlockOutputFormatter)
    OutputFormatterFactory.register_formatter("rfc4180-csv", Rfc4180CsvOutputFormatter)
    OutputFormatterFactory.register_formatter("typed-csv", TypedCsvOutputFormatter)
    OutputFormatterFactory.register_formatter("script", ScriptOutputFormatter)
    parser = argparse.ArgumentParser(description='Host Inventory Management using etcd.')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity level')
    parser.add_argument(
        "--etcd-host",
        default=Config.ETCD_DEFAULT_HOST,
        help="etcd server address (default: %(default)s)",
        dest="etcd_host",
    )
    parser.add_argument(
        "--etcd-port",
        type=int,
        default=Config.ETCD_DEFAULT_PORT,
        help="etcd server port (default: %(default)s)",
        dest="etcd_port",
    )
    parser.add_argument(
        "--etcd-base-dir",
        default=Config.ETCD_HOSTS_BASE_DIR,
        help="Base directory for host data in Etcd (default: %(default)s)",
        dest="etcd_base_dir",
    )
    parser.add_argument(
        "--format",
        choices=OutputFormatterFactory.get_available_formats(),
        default="table",
        help="Format output (default: %(default)s)",
        dest="format",
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
    logging_level = determine_logging_level(args.verbose)
    logging.basicConfig(level=logging_level)

    logging.debug("Debug mode is ON")
    logging.info("Info mode is ON")

    etcd_storage = EtcdStorage()
    print("Testing get_all_hosts directly:", etcd_storage.get_all_hosts())
    inventory = HostInventory()
    # print(inventory.get_all_hosts())
    host_manager = HostManager(inventory)

    if args.subcommand == "create":
        host_manager.create_host(args.key, args.host_data)

    elif args.subcommand == "update":
        host_manager.update_host(args.key, args.field_name, args.field_value)

    elif args.subcommand == "remove":
        host_manager.remove_host(args.key)

    elif args.subcommand == "list":
        formatted_output = host_manager.list_hosts(args.filter, args.format)
        if formatted_output:
            print(formatted_output)
        else:
            logging.error("No formatted output available")
    else:
        logging.error("Error: Subcommand is required.")
        parser.print_help()

if __name__ == "__main__":
    main()
