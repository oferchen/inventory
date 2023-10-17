#!/usr/bin/env python3
import etcd3
import argparse
import json
import tabulate
import xml.etree.ElementTree as ET


def connect_to_etcd(etcd_host, etcd_port):
    try:
        client = etcd3.client(host=etcd_host, port=etcd_port)
        return client
    except Exception as e:
        print(f"Failed to connect to etcd: {str(e)}")
        return None


def iterate_etcd_keys(client, key_prefixes):
    try:
        for key_prefix in key_prefixes:
            for key, value in client.get_prefix(key_prefix):
                yield (key.decode("utf-8"), value.decode("utf-8"))
    except Exception as e:
        print(f"Failed to iterate over etcd keys: {str(e)}")


def output_csv(key_values):
    for key, value in key_values:
        print(f"{key}, {value}")


def output_table(key_values):
    if key_values:
        headers = ["Key", "Value"]
        data = list(key_values)
        print(tabulate.tabulate(data, headers=headers, tablefmt="grid"))
    else:
        print("No key-value pairs found in etcd.")


def output_json(key_values):
    key_value_dict = dict(key_values)
    print(json.dumps(key_value_dict, indent=4))


def output_xml(key_values):
    root = ET.Element("key_values")
    for key, value in key_values:
        key_value_element = ET.SubElement(root, "key_value")
        ET.SubElement(key_value_element, "key").text = key
        ET.SubElement(key_value_element, "value").text = value
    xml_string = ET.tostring(root, encoding="unicode")
    print(xml_string)


def output(hosts, output_format):
    output_functions = {
        "csv": output_csv,
        "table": output_table,
        "json": output_json,
        "xml": output_xml,
    }


def main():
    parser = argparse.ArgumentParser(description="Iterate over key-value pairs in etcd and output their contents.")
    parser.add_argument("--etcd-host", required=True, help="etcd server address")
    parser.add_argument("--etcd-port", type=int, required=True, help="etcd server port")
    parser.add_argument("--key-prefixes", required=True, nargs="+", help="List of key prefixes to filter")
    parser.add_argument("--output", choices=["csv", "table", "json", "xml"], default="table", help="Output format")

    args = parser.parse_args()

    if client := connect_to_etcd(args.etcd_host, args.etcd_port):
        try:
            key_values = iterate_etcd_keys(client, args.key_prefixes)
            output(key_values, args.output)
        except Exception as e:
            print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
