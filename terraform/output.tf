output "SERVER_IP" {
    value = aws_instance.ubuntu.public_ip
    description = "Public IP address of the Ubuntu instance"
}