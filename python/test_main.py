# test_main.py

import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

# Import the modules/classes/functions you want to test
from main import (BlockOutputFormatter, CsvOutputFormatter, CustomException,
                  EtcdClient, HostInventory, JsonOutputFormatter,
                  OutputFormatterFactory, Rfc4180CsvOutputFormatter,
                  ScriptOutputFormatter, TableOutputFormatter,
                  TypedCsvOutputFormatter, XmlOutputFormatter, parse_host_data)


class TestYourCode(unittest.TestCase):

    def test_parse_host_data_json(self):
        # Test JSON parsing
        json_data = '{"name": "host1", "status": "online"}'
        parsed_data = parse_host_data(json_data)
        expected_data = {"name": "host1", "status": "online"}
        self.assertEqual(parsed_data, expected_data)

    def test_parse_host_data_xml(self):
        # Test XML parsing
        xml_data = '<host><name>host2</name><status>offline</status></host>'
        parsed_data = parse_host_data(xml_data)
        expected_data = {"name": "host2", "status": "offline"}
        self.assertEqual(parsed_data, expected_data)

    def test_parse_host_data_key_value(self):
        # Test key-value parsing
        kv_data = 'name=host3 status=online'
        parsed_data = parse_host_data(kv_data)
        expected_data = {"name": "host3", "status": "online"}
        self.assertEqual(parsed_data, expected_data)

    def test_etcd_client_singleton(self):
        # Test EtcdClient as a Singleton
        client1 = EtcdClient()
        client2 = EtcdClient()
        self.assertIs(client1, client2)

    def test_custom_exception(self):
        # Test CustomException
        with self.assertRaises(CustomException):
            raise CustomException("Test exception")

    def test_host_inventory_create_host(self):
        # Test HostInventory create_host method
        etcd_client = MagicMock()
        inventory = HostInventory(etcd_client)

        etcd_client.put.side_effect = lambda key, value: key + value  # Mock the etcd_client.put method

        host_data = {"name": "test-host", "status": "online"}
        result = inventory.create_host("test-host", host_data)
        expected_result = f"test-host{host_data}"
        self.assertEqual(result, expected_result)

    def test_host_inventory_update_host(self):
        # Test HostInventory update_host method
        etcd_client = MagicMock()
        inventory = HostInventory(etcd_client)

        etcd_client.put.side_effect = lambda key, value: key + value  # Mock the etcd_client.put method

        host_data = {"name": "test-host", "status": "online"}
        inventory.create_host("test-host", host_data)

        result = inventory.update_host("test-host", "status", "offline")
        expected_result = "test-host" + str({"name": "test-host", "status": "offline"})
        self.assertEqual(result, expected_result)

    def test_host_inventory_remove_host(self):
        # Test HostInventory remove_host method
        etcd_client = MagicMock()
        inventory = HostInventory(etcd_client)

        etcd_client.delete.side_effect = lambda key: key  # Mock the etcd_client.delete method

        inventory.create_host("test-host", {"name": "test-host", "status": "online"})

        result = inventory.remove_host("test-host")
        self.assertEqual(result, "test-host")

    def test_output_formatter_factory_create(self):
        # Test OutputFormatterFactory create method
        hosts = [("host1", {"status": "online"}), ("host2", {"status": "offline"})]

        formatter = OutputFormatterFactory.create("csv", hosts)
        self.assertIsInstance(formatter, CsvOutputFormatter)

        formatter = OutputFormatterFactory.create("json", hosts)
        self.assertIsInstance(formatter, JsonOutputFormatter)

        formatter = OutputFormatterFactory.create("xml", hosts)
        self.assertIsInstance(formatter, XmlOutputFormatter)

        formatter = OutputFormatterFactory.create("table", hosts)
        self.assertIsInstance(formatter, TableOutputFormatter)

        formatter = OutputFormatterFactory.create("block", hosts)
        self.assertIsInstance(formatter, BlockOutputFormatter)

        formatter = OutputFormatterFactory.create("rfc4180-csv", hosts)
        self.assertIsInstance(formatter, Rfc4180CsvOutputFormatter)

        formatter = OutputFormatterFactory.create("typed-csv", hosts)
        self.assertIsInstance(formatter, TypedCsvOutputFormatter)

        formatter = OutputFormatterFactory.create("script", hosts)
        self.assertIsInstance(formatter, ScriptOutputFormatter)

        formatter = OutputFormatterFactory.create("invalid-format", hosts)
        self.assertIsNone(formatter)

if __name__ == '__main__':
    unittest.main()
