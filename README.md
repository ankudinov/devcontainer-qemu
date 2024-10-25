# devcontainer-qemu
experiments with qemu in dev container

run:

```bash
chmod +x create_cvp_vm_files.py
./create_cvp_vm_files.py --yaml_config single_node.yml -p qwerty --deploy_yaml deploy_parameters.yml
tar -xzvf cvp-2024*
```

add bridge and more:

```bash
sudo ip link add name br0 type bridge
sudo ip link set br0 type bridge stp_state 0
sudo ip link set br0 type bridge vlan_stats_per_port 1
sudo ip addr add 192.168.122.1/24 dev br0
sudo ip link set dev br0 up
sudo mkdir /etc/qemu
echo "allow all" | sudo tee /etc/qemu/bridge.conf
echo "192.168.122.2 cvp.domain.com" | sudo tee -a /etc/hosts
```

start VM

```bash
sudo qemu-system-x86_64 -m 32G -cpu max -smp 12 -boot d -cdrom /workspaces/devcontainer-qemu/node1-cvp.iso -drive file=/workspaces/devcontainer-qemu/disk1.qcow2,format=qcow2,media=disk -drive file=/workspaces/devcontainer-qemu/disk2.qcow2,format=qcow2,media=disk -nographic -serial mon:stdio -device virtio-net-pci,netdev=user0,mac=00:0c:29:78:01:01 -netdev bridge,id=user0,br=br0
```
