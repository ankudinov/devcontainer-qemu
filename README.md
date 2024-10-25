# devcontainer-qemu
experiments with qemu in dev container

run:

  ./create_cvp_vm_files.py --yaml_config single_node.yml -p qwerty --deploy_yaml deploy_parameters.yml

add bridge:

```bash
sudo ip link add name br0 type bridge
sudo ip link set br0 type bridge stp_state 0
sudo ip link set br0 type bridge vlan_stats_per_port 1
sudo ip addr add 192.168.122.1/24 dev br0
sudo ip link set dev br0 up
```
