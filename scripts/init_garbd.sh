#!/bin/bash

yum install -y Percona-XtraDB-Cluster-garbd-57

cp /vagrant/conf/garb /etc/sysconfig/garb

systemctl enable garbd
systemctl start garbd
