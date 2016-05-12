# -*- mode: ruby -*-
# vi: set ft=ruby :

$bootstrapScript = <<SCRIPT
apt-get update && apt-get install python-pip python3 python3-pip python-nose -y
SCRIPT


VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/wily64"

  config.vm.network "public_network"

  config.vm.provision "shell", inline: $bootstrapScript
end
