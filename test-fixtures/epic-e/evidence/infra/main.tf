resource "aws_instance" "app_server" {
  ami           = "ami-demo"
  instance_type = "t3.small"
  tags = {
    Name = "app-server-node"
  }
}

resource "docker_image" "case_runtime" {
  name = "python:3.11-slim"
}
