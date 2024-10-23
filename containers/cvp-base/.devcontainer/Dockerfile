FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    qemu-kvm \
    virt-viewer \
    virt-manager \
    bridge-utils \
    libvirt-daemon \
    genisoimage \
    python3 \
    python3-pip

# copy postCreate script
COPY ./postCreate.sh /bin/postCreate.sh
RUN chmod +x /bin/postCreate.sh

# install the latest yamllint and eos-downloader
RUN pip install pyyaml \
    && pip install "eos-downloader>=0.10.3"
