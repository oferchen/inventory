package main

import (
	"context"
	"encoding/json"
	"encoding/xml"
	"flag"
	"fmt"
	"log"
	"time"

	"go.etcd.io/etcd/client/v3"
)

const (
	etcdHost = "localhost"
	etcdPort = 2379
	baseKey  = "/hosts/"
)

type Host struct {
	Name string                 `json:"name"`
	Data map[string]interface{} `json:"data"`
}

type Inventory struct {
	client *clientv3.Client
}

func NewInventory(client *clientv3.Client) *Inventory {
	return &Inventory{client}
}

func (i *Inventory) CreateHost(hostName string, hostData map[string]interface{}) error {
	key := baseKey + hostName
	host := Host{Name: hostName, Data: hostData}
	hostJSON, err := json.Marshal(host)
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_, err = i.client.Put(ctx, key, string(hostJSON))
	return err
}

func (i *Inventory) UpdateHostField(hostName, fieldName, fieldValue string) error {
	key := baseKey + hostName
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	resp, err := i.client.Get(ctx, key)
	if err != nil {
		return err
	}
	if len(resp.Kvs) == 0 {
		return fmt.Errorf("Host not found")
	}
	host := Host{}
	if err := json.Unmarshal(resp.Kvs[0].Value, &host); err != nil {
		return err
	}
	host.Data[fieldName] = fieldValue
	hostJSON, err := json.Marshal(host)
	if err != nil {
		return err
	}
	_, err = i.client.Put(ctx, key, string(hostJSON))
	return err
}

func (i *Inventory) RemoveHost(hostName string) error {
	key := baseKey + hostName
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_, err := i.client.Delete(ctx, key)
	return err
}

func (i *Inventory) ListHosts() ([]Host, error) {
	key := baseKey
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	resp, err := i.client.Get(ctx, key, clientv3.WithPrefix())
	if err != nil {
		return nil, err
	}
	hosts := make([]Host, 0)
	for _, kv := range resp.Kvs {
		host := Host{}
		if err := json.Unmarshal(kv.Value, &host); err != nil {
			return nil, err
		}
		hosts = append(hosts, host)
	}
	return hosts, nil
}

// OutputFormatter interface and formatter types

func getTypeName(data interface{}) string {
	switch data.(type) {
	case map[string]interface{}:
		return "JSON"
	case string:
		return "String"
	case int, int64, float64:
		return "Number"
	case bool:
		return "Boolean"
	default:
		return "Unknown"
	}
}

func main() {
	etcdHostFlag := flag.String("etcd-host", etcdHost, "etcd server address")
	etcdPortFlag := flag.Int("etcd-port", etcdPort, "etcd server port")
	outputFlag := flag.String("output", "table", "Output format")
	flag.Parse()

	etcdHost := *etcdHostFlag
	etcdPort := *etcdPortFlag

	etcdClient, err := getClient(etcdHost, etcdPort)
	if err != nil {
		log.Fatalf("Error initializing Etcd client: %v", err)
	}

	inventory := NewInventory(etcdClient)

	switch flag.Arg(0) {
	case "create":
		handleCreate(inventory, flag.Args()[1:])

	case "update":
		handleUpdate(inventory, flag.Args()[1:])

	case "remove":
		handleRemove(inventory, flag.Args()[1])

	case "list":
		handleList(inventory, *outputFlag)

	default:
		log.Fatal("Unknown subcommand. Use 'create', 'update', 'remove', or 'list'.")
	}
}

func getClient(host string, port int) (*clientv3.Client, error) {
	config := clientv3.Config{
		Endpoints: []string{fmt.Sprintf("%s:%d", host, port)},
	}
	return clientv3.New(config)
}

func handleCreate(inventory *Inventory, args []string) {
	if len(args) != 2 {
		log.Fatal("Usage: create <host_name> <host_data>")
	}

	hostName := args[0]
	hostDataStr := args[1]
	hostData := parseHostData(hostDataStr)

	err := inventory.CreateHost(hostName, hostData)
	if err != nil {
		log.Fatalf("Error creating host: %v", err)
	}
	log.Printf("Host '%s' created successfully!", hostName)
}

func handleUpdate(inventory *Inventory, args []string) {
	if len(args) != 3 {
		log.Fatal("Usage: update <host_name> <field_name> <field_value>")
	}

	hostName := args[0]
	fieldName := args[1]
	fieldValue := args[2]

	err := inventory.UpdateHostField(hostName, fieldName, fieldValue)
	if err != nil {
		log.Fatalf("Error updating host field: %v", err)
	}
	log.Printf("Field '%s' for host '%s' updated successfully!", fieldName, hostName)
}

func handleRemove(inventory *Inventory, hostName string) {
	err := inventory.RemoveHost(hostName)
	if err != nil {
		log.Fatalf("Error removing host: %v", err)
	}
	log.Printf("Host '%s' removed successfully!", hostName)
}

func handleList(inventory *Inventory, outputFormat string) {
	hosts, err := inventory.ListHosts()
	if err != nil {
		log.Fatalf("Error listing hosts: %v", err)
	}
	printOutput(outputFormat, hosts)
}

func printOutput(format string, hosts []Host) {
	var formatter OutputFormatter

	switch format {
	case "table":
		formatter = TableOutputFormatter{}
	case "json":
		formatter = JSONOutputFormatter{}
	case "xml":
		formatter = XMLOutputFormatter{}
	case "csv":
		formatter = CSVOutputFormatter{}
	case "block":
		formatter = BlockOutputFormatter{}
	case "rfc4180-csv":
		formatter = RFC4180CsvOutputFormatter{}
	case "typed-csv":
		formatter = TypedCsvOutputFormatter{}
	case "script":
		formatter = ScriptOutputFormatter{}
	default:
		log.Fatalf("Unknown output format: %s", format)
	}

	output := formatter.Format(hosts)
	fmt.Println(output)
}
