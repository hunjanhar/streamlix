[servers]
${ubuntu_name} ansible_host=${ubuntu_ip}
${ubuntu_name} ansible_user=${ubuntu_user}

[all:vars]
ansible_ssh_private_key_file=${ssh_key}
ansible_python_interpreter=${python_version}
ansible_host_key_checking=False
