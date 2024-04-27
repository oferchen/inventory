# Inventory

## Description
The *Inventory* project manages host information with a centralized configuration stored in etcd. It supports creating, updating, and retrieving host details, making it ideal for environments where host configurations are centrally managed and accessed programmatically.

## Key Components
- **`main.py`**: The entry point of the application, orchestrating the primary logic and interactions.
- **`etcd_client.py`**: Manages interactions with the etcd server, including operations like put, get, and delete.
- **`hostinventory.py`**: Handles functionalities for managing host inventory, such as adding and updating hosts.
- **`config.py`**: Contains configuration details for the etcd connection and other global settings.
- **`parser.py`**, **`utils.py`**: Provide utility functions for parsing data and other helper functions.
- **`inventory.py`**, **`base_formatter.py`**, **`formatters.py`**: Involved in formatting and managing the output of host data in various formats.
- **`factories.py`**, **`expressions.py`**: Support frameworks for creating and evaluating expressions, enhancing data manipulation and querying capabilities.

## Features
- **Host Management**: Perform actions like creating, updating, or removing hosts from the inventory.
- **Output Formats**: Supports multiple formats including CSV, JSON, XML, table, block, RFC4180 CSV, typed CSV, and script.
- **Dynamic Filtering**: Use logical expressions for filtering, e.g., `processor=='intel' && cores>=4`.
- **Ansible Dynamic Inventory Module**: To be developed (TBD).

### Important Note
Due to issues with the python-etcd library, the following environment variable is set if not already configured: `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`.

## Setup Instructions
1. Install the required dependencies from the `requirements.txt` file:

   `pip install -r requirements.txt`
   
2. Configure the etcd connection parameters in `config.py`.

## Configuration
Ensure the etcd host and port are correctly set in `config.py` to match your etcd server settings.

## Testing
Test the application by running the scripts provided in `test_main.py` to ensure all functionalities work as expected.

## Common Inventory Fields
The table below lists the common fields used to describe each host in the inventory:

| Field Identifier | Contents                    | Comment                           |
|------------------|-----------------------------|-----------------------------------|
| key              | hostname                    |                                   |
| monitored        | yes/no                      |                                   |
| mode             | primary role                |                                   |
| roles            | additional roles            |                                   |
| arch             | CPU architecture            |                                   |
| macaddr          | MAC address                 |                                   |
| cores            | CPU cores                   |                                   |
| cpumodel         | CPU codename                |                                   |
| swap             | swap size                   |                                   |
| tmpsize          | tmp size                    | Size of /tmp                      |
| serialnum        | enclosure serial            |                                   |
| console          | remote management           |                                   |
| mgmt type        | console management type     |                                   |
| osver            | OS version                  | e.g., alma9, rhel8                |
| backedup         | date of last backup         |                                   |
| bios             | BIOS update date            |                                   |
| ht               | hyperthreading on/off       |                                   |
| dnsdomain        | e.g., company.com           |                                   |
| release          | internal OS release string  |                                   |
| image            | deployment image string     |                                   |
| modelname        | hardware model name         |                                   |
| site             | site code                   |                                   |
| os               | OS type                     |                                   |
| ipaddr           | IP address of 1st interface |                                   |
| location         | rack location               |                                   |
| memory           | RAM MB amount               |                                   |
| owner            | company internal ownership  |                                   |
| disks            | disk size                   |                                   |
| ddate            | deployment date             |                                   |
| ssd              | swap disk                   |                                   |
| service          | distributed service name    | e.g., service name1, service name2|

## Contributing
Contributions are welcome. Please fork the repository, make your changes, and submit a pull request for review.

###### Note: This software project is still very much a work in progress.