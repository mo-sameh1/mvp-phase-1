terraform {
  required_version = ">= 1.5.0"
}

resource "aws_instance" "permit_app_server" {
  ami           = "ami-00000000000000000"
  instance_type = "t3.small"

  tags = {
    Name   = "permit-app-server"
    System = "demo-legacy-system"
  }
}

resource "aws_db_instance" "permit_database" {
  identifier = "permit-database"
  engine     = "postgres"
  db_name    = "permitdb"
}

resource "docker_image" "permit_runtime" {
  name = "example/permit-runtime:1.0"
}
