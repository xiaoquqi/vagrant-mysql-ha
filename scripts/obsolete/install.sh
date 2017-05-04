#!/bin/bash

# Installation for kolla requirements
# this is already integrated in my vagrant box

yum install -y epel-release

yum install -y python-devel libffi-devel gcc openssl-devel

# Install pip
yum install -y python-pip
pip install -U pip

# Install ansible
yum install -y ansible
pip install -U ansible

# Install docker from daocloud
curl -sSL https://get.daocloud.io/docker | sh
curl -L https://get.daocloud.io/docker/compose/releases/download/1.11.2/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
curl -sSL https://get.daocloud.io/daotools/set_mirror.sh | sh -s http://b0f4fd8f.m.daocloud.io

# Create the drop-in unit directory for docker.service
mkdir -p /etc/systemd/system/docker.service.d

# Create the drop-in unit file
tee /etc/systemd/system/docker.service.d/kolla.conf <<-'EOF'
[Service]
MountFlags=shared
EOF

# Run these commands to reload the daemon
systemctl daemon-reload
systemctl restart docker

# python docker
yum install -y python-docker-py
pip install -U docker-py

# ntp
yum install -y ntp
systemctl enable ntpd.service
systemctl start ntpd.service

# libvirt
systemctl stop libvirtd.service
systemctl disable libvirtd.service

# for kolla development
yum install -y git

# ip forward
tee /etc/sysctl.conf <<-'EOF'
net.ipv4.ip_forward=1
EOF
systemctl restart network
