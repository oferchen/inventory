# inventory
host inventory with unstructured schema using etcd

# common fields

| Field Identifier | Contents                    | Comment                           |
|------------------|-----------------------------|-----------------------------------|
| key              | hostname                   |                                   |
| monitored        | yes/no                      |                                   |
| mode             | primary Role                |                                   |
| roles            | additional Roles            |                                   |
| arch             | CPU Architecture            |                                   |
| macaddr          | MAC Address                 |                                   |
| cores            | CPU Cores                   |                                   |
| cpumodel         | CPU Codename                |                                   |
| swap             | swap Size                   |                                   |
| tmpsize          | tmp Size                    | /tmp size                         |
| serialnum        | enclosure serial            |                                   |
| console          | remote management           |                                   |
| mgmt type        | console management type     |                                   |
| osver            | os version                  | os name/version e.g. alma9, rhel8 |
| backedup         | date of last backup         |                                   |
| bios             | bios update date            |                                   |
| ht               | hyperthreading on/off       |                                   |
| dnsdomain        | e.g. company.com            |                                   |
| release          | internal os release string  |                                   |
| image            | deployment image string     |                                   |
| modelname        | hardware model name         |                                   |
| site             | site code                   |                                   |
| os               | os type                     |                                   |
| ipaddr           | ip address of 1st interface |                                   |
| location         | rack location               |                                   |
| memory           | ram mb amount               |                                   |
| owner            | company internal ownership  |                                   |
| biosdate         | bios version date           |                                   |
| disks            | disk size                   |                                   |
| ddate            | deployment date             |                                   |
| ssd              | swap disk                   |                                   |
| service          | distributed service name    |                                   |
|                  |                             |                                   |

|                  |              |         |


