#!/bin/bash

systemctl enable mysql
systemctl start mysql

GEN_ROOT_PASSWORD=$(grep 'temporary password' /var/log/mysqld.log | awk '{print $(NF)}')
ROOT_PASSWORD="sysadmin"

mysql -uroot -p"$GEN_ROOT_PASSWORD" --connect-expired-password <<-EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '$ROOT_PASSWORD';
exit
EOF

# Create replication user
mysql -uroot -p"$ROOT_PASSWORD" << EOF
CREATE USER 'sstuser'@'localhost' IDENTIFIED BY 'passw0rd';
GRANT RELOAD, LOCK TABLES, PROCESS, REPLICATION CLIENT ON *.* TO 'sstuser'@'localhost';
FLUSH PRIVILEGES;
EOF

# Create remote access for root user and create test database
mysql -uroot -p"$ROOT_PASSWORD" << EOF
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%'
    IDENTIFIED BY 'sysadmin'
    WITH GRANT OPTION;
CREATE DATABASE test;
FLUSH PRIVILEGES;
EOF

systemctl stop mysql
