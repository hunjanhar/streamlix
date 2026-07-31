resource "aws_vpc" "streamlix_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "streamlix-app-vpc" }
}

resource "aws_subnet" "streamlix_subnet" {
  vpc_id = aws_vpc.streamlix_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "ap-south-1a"
  map_public_ip_on_launch = true
  tags = { Name = "streamlix-app-public-subnet" }
}

resource "aws_internet_gateway" "streamlix_igw" {
  vpc_id = aws_vpc.streamlix_vpc.id
  tags   = { Name = "streamlix-app-igw" }
}

resource "aws_route_table" "streamlix_rt" {
  vpc_id = aws_vpc.streamlix_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.streamlix_igw.id
  }
  tags = { Name = "streamlix-route-table" }
}

resource "aws_route_table_association" "streamlix_rta" {
  subnet_id      = aws_subnet.streamlix_subnet.id
  route_table_id = aws_route_table.streamlix_rt.id
}