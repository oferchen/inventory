package main

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"encoding/xml"
	"flag"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"go.etcd.io/etcd/client/v3"
)

// KeyValue represents a key-value pair.
type KeyValue struct {
	Key   string `json:"key"`
	Value string `json:"value"`
}

func connectToEtcd(etcdHost string, etcdPort int) (*clientv3.Client, error) {
	client, err := clientv3.New(clientv3.Config{
		Endpoints:   []string{fmt.Sprintf("%s:%d", etcdHost, etcdPort)},
		DialTimeout: 5 * time.Second,
	})
	if err != nil {
		return nil, err
	}
	return client, nil
}

func iterateEtcdKeys(client *clientv3.Client, keyPrefixes []string) <-chan KeyValue {
	keyValues := make(chan KeyValue)
	ctx, cancel := context.WithCancel(context.Background())

	go func() {
		defer cancel()
		defer close(keyValues)

		for _, keyPrefix := range keyPrefixes {
			resp, err := client.Get(ctx, keyPrefix, clientv3.WithPrefix())
			if err != nil {
				log.Printf("Failed to iterate over etcd keys: %v\n", err)
				return
			}

			for _, kv := range resp.Kvs {
				keyValues <- KeyValue{Key: string(kv.Key), Value: string(kv.Value)}
			}
		}
	}()

	return keyValues
}

func outputCSV(keyValues <-chan KeyValue) {
	csvWriter := csv.NewWriter(os.Stdout)
	defer csvWriter.Flush()

	for kv := range keyValues {
		if err := csvWriter.Write([]string{kv.Key, kv.Value}); err != nil {
			log.Fatalf("Error writing CSV: %v\n", err)
		}
	}
}

func outputTable(keyValues <-chan KeyValue) {
	fmt.Println("Key\tValue")
	for kv := range keyValues {
		fmt.Printf("%s\t%s\n", kv.Key, kv.Value)
	}
}

func outputJSON(keyValues <-chan KeyValue) {
	keyValueSlice := []KeyValue{}
	for kv := range keyValues {
		keyValueSlice = append(keyValueSlice, kv)
	}

	jsonBytes, err := json.MarshalIndent(keyValueSlice, "", "    ")
	if err != nil {
		log.Fatalf("Error marshaling JSON: %v\n", err)
	}

	fmt.Println(string(jsonBytes))
}

func outputXML(keyValues <-chan KeyValue) {
	keyValueSlice := []KeyValue{}
	for kv := range keyValues {
		keyValueSlice = append(keyValueSlice, kv)
	}

	output := struct {
		XMLName xml.Name `xml:"key_values"`
		Data    []KeyValue
	}{Data: keyValueSlice}

	xmlBytes, err := xml.MarshalIndent(output, "", "    ")
	if err != nil {
		log.Fatalf("Error marshaling XML: %v\n", err)
	}

	fmt.Println(xml.Header + string(xmlBytes))
}

func main() {
	etcdHost := flag.String("etcd-host", "", "etcd server address")
	etcdPort := flag.Int("etcd-port", 0, "etcd server port")
	keyPrefixes := flag.String("key-prefixes", "", "List of key prefixes to filter (comma-separated)")
	outputFormat := flag.String("output", "table", "Output format (csv, table, json, xml)")

	flag.Parse()

	if *etcdHost == "" || *etcdPort == 0 || *keyPrefixes == "" {
		log.Fatal("etcd-host, etcd-port, and key-prefixes are required")
	}

	client, err := connectToEtcd(*etcdHost, *etcdPort)
	if err != nil {
		log.Fatalf("Failed to connect to etcd: %v\n", err)
	}
	defer client.Close()

	keyPrefixList := strings.Split(*keyPrefixes, ",")
	keyValues := iterateEtcdKeys(client, keyPrefixList)

	switch *outputFormat {
	case "csv":
		outputCSV(keyValues)
	case "table":
		outputTable(keyValues)
	case "json":
		outputJSON(keyValues)
	case "xml":
		outputXML(keyValues)
	default:
		log.Fatalf("Invalid output format: %s\n", *outputFormat)
	}
}
