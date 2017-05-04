# How to use this project

This project is to help to build an HA environment based on Percona XtraDB offical document.

Also provide a repaire scripts to help administrator to fix the cluster for poweroff abnormally.

# Vagrant Box

Vagrant Box can be downloaded from baidu net disk: 

Link: https://pan.baidu.com/s/1hrTUMjE
Password: c93s

Use vagrant add to add box:

    vagrant box add Percona-XtraDB-Cluster.box --name Percona-XtraDB-Cluster
    
This box is already installed Percona-XtraDB and salt package, so you don't need internet for build cluster.

# Start Cluster

Run this script to start mysql cluster

    ./create_mysql_ha.sh
    
# Repair Cluster

Run this script to repair mysql cluster:

    ./scripts/repaire_mysql_cluster.py
