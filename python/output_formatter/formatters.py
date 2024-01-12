# output_formatter/formatters.py
import csv
import json
import logging
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Tuple

import tabulate

from .base_formatter import BaseOutputFormatter


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
        host_dict = dict(self.hosts)
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
