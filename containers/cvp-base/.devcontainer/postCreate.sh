#!/usr/bin/env bash

set +e

# sudo ip link add name br0 type bridge
# sudo ip link set br0 type bridge stp_state 0
# sudo ip link set br0 type bridge vlan_stats_per_port 1
# sudo ip addr add 192.168.122.1/24 dev br0
# sudo ip link set dev br0 up
sudo mkdir /etc/qemu
echo "allow all" | sudo tee /etc/qemu/bridge.conf

ardl get cvp --format kvm --version ${CVP_VERSION}

tar -xzvf cvp-2024* -C /tmp
mv node1-cvp.iso /tmp/
