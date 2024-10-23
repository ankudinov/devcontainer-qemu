#!/usr/bin/env python3
from crypt import crypt
import os
import argparse
import getpass
from random import Random, random
import yaml
import sys
import tempfile
import subprocess
import shlex
import shutil
import random
import crypt
import xml.etree.ElementTree as ET
import uuid

MIN_CPU = 8
MIN_RAM_MB = 22528


def read_yaml_file(filename, load_all=False):
    with open(filename, mode='r') as f:
        if not load_all:
            yaml_data = yaml.load(f, Loader=yaml.FullLoader)
        else:
            # convert generator to list before returning
            yaml_data = list(yaml.load_all(f, Loader=yaml.FullLoader))
    return yaml_data


def readPassword():
    print("Please enter a password for root user on cvp")
    while True:
        password = getpass.getpass()
        passRepeat = getpass.getpass("Please re-enter the password: ")
        if password == passRepeat:
            return password
        print("Passwords don't match, please retry")


def parseArgs():
    parser = argparse.ArgumentParser(description='Deploy CVP on KVM')
    parser.add_argument('-y', '--yaml_config',
                        help='Single- or multinode YAML config file', required=True)
    parser.add_argument('-p', '--password',
                        help="Password for the root user. If no password is "
                              "given then prompt for the password.")
    parser.add_argument('-dy', '--deploy_yaml',
                        help='YAML file with parameters to deploy CVP VMs on KVM.', required=True)
    args = parser.parse_args()

    # set output directory and create if it does not exist
    args.outdir = "cvp-deploy-files"
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    # get password from user input if not yet defined
    if not args.password:
        args.password = readPassword()

    return args


class CvpConfigParser:

    def __init__(self, yaml_filename) -> None:
        try:
            self.config = read_yaml_file(yaml_filename)
        except Exception as _:
            sys.exit(f'ERROR: Can not load {yaml_filename}')

        if not isinstance(self.config, dict):
            sys.exit(
                f'ERROR: config loaded from {yaml_filename} is not a dictionary.')
        else:
            # check if mandatory keys are present
            if not (
                ('common' in self.config.keys()) and (
                    'node1' in self.config.keys())
            ):
                sys.exit(
                    'ERROR: configuration file must have at least "common" and "node1" keys.')

    def nodes(self) -> list:
        """Returns list of node dictionaries

        Returns:
            list: list of node dictionaries
        """
        return [{k: v} for k, v in self.config.items() if 'node' in k]

    def nodeCnt(self) -> int:
        """Returns number of nodes

        Returns:
            int: number of nodes
        """
        return len(self.nodes())


def genIso(args) -> None:
    """Generate files required to deploy CVP VMs on KVM
    """
    # load and parse cluster config
    cluster_config = CvpConfigParser(args.yaml_config)

    # Generate CDROM ISO for each node in the cluster.
    # Each ISO will be named: node<n>-<vmname>.iso
    # Each ISO will contain:
    # 1. cvp-config.yaml: An exact copy of the YAML file passed in.
    # 2. nodename.txt: Name of the node that the ISO should be loaded on.
    # 3. id_rsa: private key, same content in all ISOs
    # 4. id_rsa.pub: public key, same content in all ISOs
    # 5. password: The hashed password to stuff into /etc/shadow. Note that the
    #              password is the same for all nodes, but the hash is unique for
    #              each node

    # generate private key
    id_rsa = tempfile.NamedTemporaryFile()
    id_rsa.close()
    cmd = shlex.split(f'ssh-keygen -t rsa -f {id_rsa.name} -N "" -q')
    res = subprocess.run(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    if res.returncode != 0:
        sys.exit('ERROR: can not create SSH key.')

    isoFiles = list()
    for node in cluster_config.nodes():
        node_key = list(node.keys())[0]
        tempDir = tempfile.mkdtemp()
        node_hostname = node[node_key]['hostname'].partition('.')[0]
        isoname = f'{node_key}-{node_hostname}.iso'
        isopath = f'{args.outdir}/{isoname}'
        print(f'Building ISO for {node_key} {node_hostname}: {isopath}')

        shutil.copyfile(
            args.yaml_config, os.path.join(tempDir, 'cvp-config.yaml')
        )
        with open(os.path.join(tempDir, 'nodename.txt'), 'w') as nodenameFile:
            nodenameFile.write(f'{node_key}\n')
        shutil.copyfile(id_rsa.name, os.path.join(tempDir, 'id_rsa'))
        shutil.copyfile(f'{id_rsa.name}.pub',
                        os.path.join(tempDir, 'id_rsa.pub'))
        os.chmod(os.path.join(tempDir, 'id_rsa'), 0o600)
        os.chmod(os.path.join(tempDir, 'id_rsa.pub'), 0o600)

        # generate password file if password was defined by user
        # ignore if password was not defined
        if args.password:
            with open(os.path.join(tempDir, 'password'), 'w') as passwordFile:
                # This is a floating point number, it still serves our purpose
                salt = str(random.random())
                passwordFile.write(
                    crypt.crypt(args.password, f'$6${salt}')
                )

        cmd = shlex.split(
            f'genisoimage -input-charset utf-8 -l -r -iso-level 3 -o {isopath} {tempDir}')
        res = subprocess.run(cmd, stdout=subprocess.PIPE,
                             universal_newlines=True)
        if res.returncode != 0:
            sys.exit(f'ERROR: Can not create ISO file {isopath}.')

        # cmd = shlex.split(
        #     f'sudo qemu-img convert -o compat=1.1 -c -p -O qcow2 {isopath} {args.outdir}/{node_key}-{node_hostname}.qcow2')
        # res = subprocess.run(cmd, stdout=subprocess.PIPE,
        #                      universal_newlines=True)
        # if res.returncode != 0:
        #     sys.exit(f'ERROR: Can not create ISO file {isopath}.')
        # os.remove(isopath)
        shutil.rmtree(tempDir)
        isoFiles.append(isopath)

    os.unlink(id_rsa.name)
    os.unlink(f'{id_rsa.name}.pub')
    return isoFiles


def genXmlForKvm(args):
    # load deploy config
    try:
        deploy_config = read_yaml_file(args.deploy_yaml)
    except Exception as _:
        sys.exit(f'ERROR: Can not load {args.deploy_yaml}')
    # load and parse cluster config
    cluster_config = CvpConfigParser(args.yaml_config)
    for node in cluster_config.nodes():
        # find node hostname
        node_key = list(node.keys())[0]
        node_hostname = node[node_key]['hostname'].partition('.')[0]
        # define target path on KVM host for images
        image_name_prefix = f'{node_key}-{node_hostname}'
        cdrom_image_path = f'{deploy_config["libvirt_image_directory"]}/{image_name_prefix}.iso'
        disk1_image_path = f'{deploy_config["libvirt_image_directory"]}/{image_name_prefix}-disk1.qcow2'
        disk2_image_path = f'{deploy_config["libvirt_image_directory"]}/{image_name_prefix}-disk2.qcow2'
        # load original XML template
        xml_template_file = "cvpTemplate.xml"
        xml_root = None
        if os.access(xml_template_file, os.F_OK | os.R_OK):
            xml_tree = ET.parse(xml_template_file)
            xml_root = xml_tree.getroot()
        if xml_root is None:
            sys.exit(
                f'ERROR: can not load XML template file {xml_template_file}')
        # set disk path for the VM
        for child in xml_root.iter('devices'):
            for disk in child.iter('disk'):
                # set disk1 path
                if disk.find('target').attrib['dev'] in ['hda', 'vda']:
                    disk.find('source').attrib['file'] = disk1_image_path
                # set disk2 path
                elif disk.find('target').attrib['dev'] in ['hdb', 'vdb']:
                    disk.find('source').attrib['file'] = disk2_image_path
                # set cdrom path for ISO based provisioning
                elif disk.attrib['device'] == 'cdrom':
                    disk.find('source').attrib['file'] = cdrom_image_path
                    # for child in xml_root.iter('os'):
                    #     child.find('boot').attrib['dev'] = 'cdrom'

        # set VM bridge
        # current version supports single bridge per VM instead of device bridge and cluster bridge
        # as majority of the virtualized CVP deployments use single bridge
        for child in xml_root.iter('interface'):
            for c in child.iter('source'):
                if c.attrib['bridge'] == '@device_bridge_name@':
                    c.attrib['bridge'] = deploy_config['bridge_name']

        # set VM name
        xml_root.find('name').text = node_hostname

        # set qemu path
        for child in xml_root.iter('devices'):
            if 'qemu_path' in deploy_config.keys():
                child.find('emulator').text = str(deploy_config['qemu_path'])
            else:
                child.find('emulator').text = '/usr/bin/qemu-kvm'

        # set uuid
        xml_root.find('uuid').text = str(uuid.uuid4())

        # set VM ID
        if 'vm_id' in deploy_config.keys():
            xml_root.attrib['id'] = str(deploy_config['vm_id'])
        else:
            xml_root.attrib['id'] = 100

        # set CPU count
        if 'cpu_count' in deploy_config.keys():
            if int(deploy_config['cpu_count']) < MIN_CPU:
                print(
                    f'{deploy_config["cpu_count"]} cpu cores may not suffice. We recommend {MIN_CPU} cpu cores for optimal performance.')
            xml_root.find('vcpu').text = str(deploy_config['cpu_count'])
        else:
            xml_root.find('vcpu').text = str(MIN_CPU)

        # set RAM
        if 'ram' in deploy_config.keys():
            if int(deploy_config['ram']) < MIN_RAM_MB:
                print(
                    f'{deploy_config["am"]} MB RAM may not suffice. We recommend {MIN_RAM_MB} MB for optimal performance.')
            xml_root.find('memory').text = str(deploy_config['ram'])
            xml_root.find('currentMemory').text = str(deploy_config['ram'])
        else:
            xml_root.find('memory').text = str(MIN_RAM_MB)
            xml_root.find('currentMemory').text = str(MIN_RAM_MB)

        # write final XML for the VM
        xml_tree.write(f'{args.outdir}/{image_name_prefix}.xml')


if __name__ == '__main__':
    # parse CLI arguments
    args = parseArgs()
    # generate CDROM ISO files
    genIso(args)
    # generate XML templates for CVP VMs
    genXmlForKvm(args)
