#!/bin/bash

# Install ntp service
yum install -y wget ntp
systemctl enable ntpd
systemctl start ntpd

tee /etc/yum.repos.d/percona-release.repo <<-'EOF'
[percona]
name = percona
baseurl = https://mirrors.tuna.tsinghua.edu.cn/percona/release/7/RPMS/x86_64
enabled = 1
gpgcheck = 0
EOF

tee /etc/yum.repos.d/salt-latest.repo <<-'EOF'
[salt-latest]
name=SaltStack Latest Release Channel for RHEL/Centos 7
baseurl=https://mirrors.tuna.tsinghua.edu.cn/saltstack/yum/redhat/7/x86_64/latest/
failovermethod=priority
enabled=1
gpgcheck=0
EOF

yum install -y Percona-XtraDB-Cluster-57

tee -a /etc/hosts <<-'EOF'
db1 200.21.1.161
db2 200.21.1.162
db3 200.21.1.163
EOF

# Salt installation and configuration

HOSTNAME=$(hostname)
if [[ $HOSTNAME =~ "db1" ]]; then
  yum install -y salt-master
  if [[ -e "/etc/salt/master" ]]; then
    sed -i 's/#interface: 0.0.0.0/interface: 0.0.0.0/' /etc/salt/master
    sed -i 's/#auto_accept: False/auto_accept: True/' /etc/salt/master
  #  cat << EOF | tee -a /etc/salt/master
  #file_roots:
  #  base:
  #    - /vagrant/salt-ec-cloud/salt
  #EOF
  #  cat << EOF | tee -a /etc/salt/master
  #pillar_roots:
  #  base:
  #      - /vagrant/salt-ec-cloud/pillar
  #EOF
    systemctl enable salt-master
    systemctl start salt-master
  fi
fi

yum install -y salt-minion
if [[ -e "/etc/salt/minion" ]]; then
  sed -i 's/#master: salt/master: 200.21.1.161/' /etc/salt/minion
  sed -i 's/#log_level: warning/log_level: debug/' /etc/salt/minion
  systemctl enable salt-minion
  systemctl start salt-minion
fi

# for salt psutils
yum install -y psutils python-psutil

