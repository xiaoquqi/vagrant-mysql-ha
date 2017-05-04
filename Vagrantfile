# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "Percona-XtraDB-Cluster"

  config.vm.provider :virtualbox do |vb|
    # Use VBoxManage to customize the VM. For example to change memory:
    vb.memory = 2048
    vb.cpus = 2
  end

  (1..3).each do |i|
    config.vm.define "mysql-ha#{i}" do |node|
      node.vm.hostname = "db#{i}.mysql.com"
      node.vm.network "public_network", ip: "200.21.1.16#{i}", netmask: "255.255.0.0", bridge: "enp3s0"
    end # end config.vm.define
  end # (1..3).each

  config.vm.define "garbd" do |node|
    node.vm.hostname = "garbd.mysql.com"
    node.vm.network "public_network", ip: "200.21.1.164", netmask: "255.255.0.0", bridge: "enp3s0"
  end # end config.vm.define

  config.vm.provision :shell, :path => "scripts/init.sh"
end
