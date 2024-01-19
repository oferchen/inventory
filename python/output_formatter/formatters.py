# output_formatter/formatters.py
import csv
import io
import json
import logging
import sys
import xml.etree.ElementTree as ET
from itertools import chain
from typing import Any, Dict, List, Tuple

import tabulate

from .base_formatter import BaseOutputFormatter


# CSV Output Formatter
class CsvOutputFormatter(BaseOutputFormatter):
    def format_data(self) -> Dict[str, str]:
        if self.hosts is None or not self.hosts:
            return {"formatted_data": ""}
        output_stream = io.StringIO()
        all_keys = {key for host_data in self.hosts.values() for key in host_data}
        headers = ["Host Name"] + sorted(all_keys)
        writer = csv.DictWriter(output_stream, fieldnames=headers)
        writer.writeheader()
        for host_name, host_data in self.hosts.items():
            row = {'Host Name': host_name, **host_data}
            writer.writerow(row)
        return {"formatted_data": output_stream.getvalue()}


# JSON Output Formatter
class JsonOutputFormatter(BaseOutputFormatter):
    def format_data(self) -> Dict[str, str]:
        print(f"Debug: Formatting data for JSON: {self.hosts}")
        return {"formatted_data": json.dumps(self.hosts, indent=4) if self.hosts else '{}'}

# XML Output Formatter
class XmlOutputFormatter(BaseOutputFormatter):
    def format_data(self) -> Dict[str, str]:
        root = ET.Element("hosts")
        for host_name, host_data in self.hosts.items():
            host_element = ET.SubElement(root, "host", name=host_name)
            for key, value in host_data.items():
                attribute = ET.SubElement(host_element, key)
                attribute.text = str(value)
        xml_string = ET.tostring(root, encoding="unicode")
        return {"formatted_data": xml_string}


class TableOutputFormatter(BaseOutputFormatter):
    def format_data(self) -> Dict[str, str]:
        if not self.hosts:
            return {"formatted_data": ""}

        all_keys = set(chain.from_iterable(self.hosts[host].keys() for host in self.hosts))
        headers = ["Name"] + sorted(all_keys)

        table_data = []
        for host_name, host_data in self.hosts.items():
            row = {'Name': host_name} | {
                key: host_data.get(key, '') for key in sorted(all_keys)
            }
            table_data.append(row)

        logging.debug(f"Headers: {headers}")
        logging.debug(f"Table Data: {table_data}")

        table_string = tabulate.tabulate(table_data, headers=headers, tablefmt="grid")
        return {"formatted_data": table_string}


# Block Output Formatter
class BlockOutputFormatter(BaseOutputFormatter):
    def format_data(self) -> Dict[str, str]:
        if not self.hosts:
            return {"formatted_data": ""}
        blocks = []
        for host_name, host_data in self.hosts.items():
            block = f"Host: {host_name}\n" + "\n".join(f"  {key}: {value}" for key, value in host_data.items())
            blocks.append(block)
        return {"formatted_data": "\n".join(blocks)}


# RFC 4180-compliant CSV Output Formatter
class Rfc4180CsvOutputFormatter(BaseOutputFormatter):
    def format_data(self) -> Dict[str, str]:
        output_stream = io.StringIO()
        all_keys = {key for host_data in self.hosts.values() for key in host_data}
        headers = ["Host Name"] + sorted(all_keys)
        writer = csv.DictWriter(output_stream, fieldnames=headers, dialect='excel')
        writer.writeheader()
        for host_name, host_data in self.hosts.items():
            row = {'Host Name': host_name, **host_data}
            writer.writerow(row)
        return {"formatted_data": output_stream.getvalue()}


# Typed CSV Output Formatter
class TypedCsvOutputFormatter(BaseOutputFormatter):
    def format_data(self) -> Dict[str, str]:
        output_stream = io.StringIO()
        writer = csv.writer(output_stream)
        writer.writerow(["Host Name", "Host Data Type", "Host Data"])
        for host_name, host_data in self.hosts.items():
            data_type = type(host_data).__name__
            writer.writerow([host_name, data_type, json.dumps(host_data)])
        return {"formatted_data": output_stream.getvalue()}


# Script Output Formatter (CSV without header)
class ScriptOutputFormatter(BaseOutputFormatter):
    def format_data(self) -> Dict[str, str]:
        output_stream = io.StringIO()
        writer = csv.writer(output_stream, quoting=csv.QUOTE_NONE)
        for host_name, host_data in self.hosts.items():
            writer.writerow([host_name, json.dumps(host_data)])
        return {"formatted_data": output_stream.getvalue()}
