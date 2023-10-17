#!/usr/bin/env python3
import etcd3
import argparse
import sys
import json
import tabulate
import xml.etree.ElementTree as ET


class HostInventory:
    def __init__(self, etcd_host, etcd_port):
        self.client = etcd3.client(host=etcd_host, port=etcd_port)
        self.base_key = "/hosts/"

    def _build_key(self, host_name):
        return f"{self.base_key}{host_name}"

    def create_host(self, host_name, host_data):
        key = self._build_key(host_name)
        try:
            self.client.put(key, json.dumps(host_data))
        except Exception as e:
            print(f"Failed to add host: {str(e)}")
            sys.exit(1)

    def modify_host(self, host_name, field_name, field_value):
        key = self._build_key(host_name)
        try:
            host_data = self.get_host_data(host_name)
            if host_data is not None:
                host_data[field_name] = field_value
                self.client.put(key, json.dumps(host_data))
                print(f"Updated field '{field_name}' for host '{host_name}'")
            else:
                print(f"Host '{host_name}' not found.")
        except Exception as e:
            print(f"Failed to update host: {str(e)}")
            sys.exit(1)

    def remove_host(self, host_name):
        key = self._build_key(host_name)
        try:
            self.client.delete(key)
            print(f"Host '{host_name}' removed successfully!")
        except Exception as e:
            print(f"Failed to remove host: {str(e)}")
            sys.exit(1)

    def list_hosts(self):
        try:
            hosts = []
            for key, value in self.client.get_prefix(self.base_key):
                host_name = key.decode("utf-8").replace(self.base_key, "")
                host_data = json.loads(value.decode("utf-8"))
                hosts.append((host_name, host_data))
            return hosts
        except Exception as e:
            print(f"Failed to list hosts: {str(e)}")
            sys.exit(1)

    def get_host_data(self, host_name):
        key = self._build_key(host_name)
        _, value = self.client.get(key)
        return json.loads(value.decode("utf-8")) if value else None


def output_csv(hosts):
    for host_name, host_data in hosts:
        print(f"{host_name}, {json.dumps(host_data)}")


def output_table(hosts):
    if hosts:
        headers = ["Host Name", "Host Data"]
        data = [(host_name, json.dumps(host_data)) for host_name, host_data in hosts]
        print(tabulate.tabulate(data, headers=headers, tablefmt="grid"))
    else:
        print("No hosts found in the inventory.")


def output_json(hosts):
    host_dict = dict(hosts)
    print(json.dumps(host_dict, indent=4))


def output_xml(hosts):
    root = ET.Element("hosts")
    for host_name, host_data in hosts:
        host_element = ET.SubElement(root, "host")
        ET.SubElement(host_element, "name").text = host_name
        ET.SubElement(host_element, "data").text = json.dumps(host_data)
    xml_string = ET.tostring(root, encoding="unicode")
    print(xml_string)


def output(hosts, output_format):
    output_functions = {
        "csv": output_csv,
        "table": output_table,
        "json": output_json,
        "xml": output_xml,
    }

    if output_format in output_functions:
        output_function = output_functions[output_format]
        output_function(hosts)
    else:
        print(f"Unsupported output format: {output_format}")


def main():
    parser = argparse.ArgumentParser(description="Manage a host inventory using etcd.")
    parser.add_argument("--etcd-host", required=True, help="etcd server address")
    parser.add_argument("--etcd-port", type=int, required=True, help="etcd server port")
    parser.add_argument("--output", choices=["csv", "table", "json", "xml"], default="table", help="Output format")

    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

    create_parser = subparsers.add_parser("create", help="Create a host")
    create_parser.add_argument("host_name", help="Host name")
    create_parser.add_argument("host_data", help="Host data in JSON, XML, or key-value format")

    modify_parser = subparsers.add_parser("modify", help="Modify a host field")
    modify_parser.add_argument("host_name", help="Host name")
    modify_parser.add_argument("field_name", help="Field name")
    modify_parser.add_argument("field_value", help="Field value")

    remove_parser = subparsers.add_parser("remove", help="Remove a host")
    remove_parser.add_argument("host_name", help="Host name to remove")

    list_parser = subparsers.add_parser("list", help="List all hosts")

    args = parser.parse_args()

    inventory = HostInventory(args.etcd_host, args.etcd_port)

    if args.subcommand == "create":
        host_data = args.host_data

        # Detect the format of host data and parse accordingly
        try:
            if host_data.startswith("{") and host_data.endswith("}"):
                # JSON format
                host_data = json.loads(host_data)
            elif "<" in host_data and ">" in host_data:
                # XML format
                root = ET.fromstring(host_data)
                host_data = {elem.tag: elem.text for elem in root}
            else:
                # Key-value pairs format
                host_data = dict(item.split("=", 1) for item in host_data.split())
        except Exception as e:
            print(f"Failed to parse host data: {str(e)}")
            sys.exit(1)

        inventory.create_host(args.host_name, host_data)
        print("Host created successfully!")

    elif args.subcommand == "modify":
        inventory.modify_host(args.host_name, args.field_name, args.field_value)

    elif args.subcommand == "remove":
        inventory.remove_host(args.host_name)

    elif args.subcommand == "list":
        hosts = inventory.list_hosts()
        output(hosts, args.output)


if __name__ == "__main__":
    main()
