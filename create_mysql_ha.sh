#!/bin/bash

# This script is to help to build mysql ha cluster based on
# Percona-XtraDB-Cluster

#db1 200.21.1.161
#db2 200.21.1.162
#db3 200.21.1.163

# Start first node
vagrant up mysql-ha1

vagrant ssh mysql-ha1 << EOF
sudo -s
cp /vagrant/scripts/init_mysql.sh /root
chmod +x /root/init_mysql.sh
/root/init_mysql.sh
cat /vagrant/conf/my.cnf | tee -a /etc/my.cnf
EOF

vagrant up mysql-ha2
vagrant ssh mysql-ha2 << EOF
sudo -s
cat /vagrant/conf/my.cnf | tee -a /etc/my.cnf
sed -i "s|wsrep_node_name=pxc1|wsrep_node_name=pxc2|g" /etc/my.cnf
sed -i "s|wsrep_node_address=200.21.1.161|wsrep_node_address=200.21.1.162|g" /etc/my.cnf
EOF

vagrant up mysql-ha3
vagrant ssh mysql-ha3 << EOF
sudo -s
cat /vagrant/conf/my.cnf | tee -a /etc/my.cnf
sed -i "s|wsrep_node_name=pxc1|wsrep_node_name=pxc3|g" /etc/my.cnf
sed -i "s|wsrep_node_address=200.21.1.161|wsrep_node_address=200.21.1.163|g" /etc/my.cnf
EOF

vagrant ssh mysql-ha1 << EOF
sudo -s
systemctl start mysql@bootstrap.service
EOF

vagrant ssh mysql-ha2 << EOF
sudo -s
systemctl start mysql
EOF

vagrant ssh mysql-ha3 << EOF
sudo -s
systemctl start mysql
EOF

#vagrant up garbd

#vagrant ssh garbd << EOF
#sudo -s
#cp /vagrant/scripts/init_garbd.sh /root
#chmod +x /root/init_garbd.sh
#/root/init_garbd.sh
#EOF
