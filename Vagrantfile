Vagrant.configure("2") do |config|
    # Define the base box
    config.vm.box = "generic/ubuntu2004"  # You can choose a different box as needed
  
    # Provider-specific configuration
    config.vm.provider :libvirt do |libvirt|
      libvirt.memory = 2048
      libvirt.cpus = 2
    end
  
    # Provisioning scripts (if any)
    # For example, setting up Python and Geopandas
    config.vm.provision "shell", inline: <<-SHELL
      sudo apt-get update
      sudo apt-get install -y python3 python3-pip
      sudo pip3 install geopandas
      # Add other necessary packages or setup steps here
    SHELL
  end
  