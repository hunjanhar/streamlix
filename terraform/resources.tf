resource "local_file" "ansible_inventory" {
  filename = "${path.module}/hosts.ini"
  
  content = templatefile("${path.module}/inventary.tpl", {
    ubuntu_name     = aws_instance.ubuntu.tags["Name"]
    ubuntu_ip       = aws_instance.ubuntu.public_ip
    ubuntu_user     = "ubuntu"
    ssh_key         = "${path.module}/streamlix-app-ec2"
    python_version  = "/usr/bin/python3"
  })
}

resource "null_resource" "run_ansible" {
  depends_on = [
    local_file.ansible_inventory, 
    aws_instance.ubuntu
  ]

  triggers = {
    ubuntu_ip = aws_instance.ubuntu.public_ip
  }

  provisioner "remote-exec" {
    inline = ["echo 'SSH is up and running!'"]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("${path.module}/streamlix-app-ec2")
      host        = aws_instance.ubuntu.public_ip
    }
  }

  provisioner "local-exec" {
    command = "ansible-playbook -i hosts.ini playbooks/config.yml"
  }
}