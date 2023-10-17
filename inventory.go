package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"strings"

	"go.etcd.io/etcd/client/v3"
	"golang.org/x/net/context"
)

type HostInventory struct {
	client  *clientv3.Client
	baseKey string
}

func NewHostInventory(etcdHost string, etcdPort int) (*HostInventory, error) {
	endpoints := []string{fmt.Sprintf("%s:%d", etcdHost, etcdPort)}
	client, err := clientv3.New(clientv3.Config{
		Endpoints: endpoints,
	})
	if err != nil {
		return nil, err
	}

	return &HostInventory{
		client:  client,
		baseKey: "/hosts/",
	}, nil
}

func (h *HostInventory) Close() {
	h.client.Close()
}

func (h *HostInventory) buildKey(hostName string) string {
	return h.baseKey + hostName
}

func (h *HostInventory) CreateHost(hostName string, hostData map[string]interface{}) error {
	key := h.buildKey(hostName)
	hostDataBytes, err := json.Marshal(hostData)
	if err != nil {
		return err
	}

	_, err = h.client.Put(context.TODO(), key, string(hostDataBytes))
	return err
}

func (h *HostInventory) ModifyHost(hostName string, fieldName string, fieldValue string) error {
	key := h.buildKey(hostName)

	// Retrieve current host data
	resp, err := h.client.Get(context.TODO(), key)
	if err != nil {
		return err
	}

	if len(resp.Kvs) == 0 {
		return fmt.Errorf("Host '%s' not found", hostName)
	}

	// Unmarshal the existing host data
	var hostData map[string]interface{}
	if err := json.Unmarshal(resp.Kvs[0].Value, &hostData); err != nil {
		return err
	}

	// Update the specified field
	hostData[fieldName] = fieldValue

	// Marshal and update the host data
	hostDataBytes, err := json.Marshal(hostData)
	if err != nil {
		return err
	}

	_, err = h.client.Put(context.TODO(), key, string(hostDataBytes))
	if err != nil {
		return err
	}

	fmt.Printf("Updated field '%s' for host '%s'\n", fieldName, hostName)
	return nil
}

func (h *HostInventory) RemoveHost(hostName string) error {
	key := h.buildKey(hostName)

	_, err := h.client.Delete(context.TODO(), key)
	if err != nil {
		return err
	}

	fmt.Printf("Host '%s' removed successfully!\n", hostName)
	return nil
}

func (h *HostInventory) ListHosts() ([]string, error) {
	prefix := h.baseKey
	resp, err := h.client.Get(context.TODO(), prefix, clientv3.WithPrefix())
	if err != nil {
		return nil, err
	}

	var hostNames []string
	for _, kv := range resp.Kvs {
		hostName := strings.TrimPrefix(string(kv.Key), prefix)
		hostNames = append(hostNames, hostName)
	}

	return hostNames, nil
}

func main() {
	etcdHost := flag.String("etcd-host", "", "etcd server address")
	etcdPort := flag.Int("etcd-port", 0, "etcd server port")
	outputFormat := flag.String("output", "table", "Output format")
	flag.Parse()

	if *etcdHost == "" || *etcdPort == 0 {
		log.Fatal("etcd-host and etcd-port must be provided")
	}

	inventory, err := NewHostInventory(*etcdHost, *etcdPort)
	if err != nil {
		log.Fatalf("Failed to create inventory: %v", err)
	}
	defer inventory.Close()

	switch flag.Arg(0) {
	case "create":
		hostName := flag.Arg(1)
		hostDataStr := flag.Arg(2)
		var hostData map[string]interface{}

		// Detect the format of host data and parse accordingly
		if strings.HasPrefix(hostDataStr, "{") && strings.HasSuffix(hostDataStr, "}") {
			// JSON format
			if err := json.Unmarshal([]byte(hostDataStr), &hostData); err != nil {
				log.Fatalf("Failed to parse host data: %v", err)
			}
		} else {
			// Key-value pairs format
			keyValuePairs := strings.Split(hostDataStr, " ")
			hostData = make(map[string]interface{})
			for _, kv := range keyValuePairs {
				parts := strings.SplitN(kv, "=", 2)
				if len(parts) == 2 {
					hostData[parts[0]] = parts[1]
				}
			}
		}

		if err := inventory.CreateHost(hostName, hostData); err != nil {
			log.Fatalf("Failed to create host: %v", err)
		}
		fmt.Println("Host created successfully!")

	case "modify":
		hostName := flag.Arg(1)
		fieldName := flag.Arg(2)
		fieldValue := flag.Arg(3)

		if err := inventory.ModifyHost(hostName, fieldName, fieldValue); err != nil {
			log.Fatalf("Failed to modify host: %v", err)
		}

	case "remove":
		hostName := flag.Arg(1)

		if err := inventory.RemoveHost(hostName); err != nil {
			log.Fatalf("Failed to remove host: %v", err)
		}

	case "list":
		hostNames, err := inventory.ListHosts()
		if err != nil {
			log.Fatalf("Failed to list hosts: %v", err)
		}

		switch *outputFormat {
		case "json":
			hostNamesJSON, _ := json.Marshal(hostNames)
			fmt.Println(string(hostNamesJSON))

		case "csv":
			fmt.Println(strings.Join(hostNames, ","))

		case "table":
			fmt.Println("Host Names:")
			for _, hostName := range hostNames {
				fmt.Println(hostName)
			}

		default:
			fmt.Printf("Unsupported output format: %s\n", *outputFormat)
		}

	default:
		fmt.Println("Invalid command. Supported commands: create, modify, remove, list")
		os.Exit(1)
	}
}
