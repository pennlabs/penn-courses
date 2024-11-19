provider "aws" {
  region = "us-east-1"
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.72.1"
    }
  }
}

output "backend-url" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

locals {
  envs = { for tuple in regexall("(.*)=(.*)", file("deploy.env")) : tuple[0] => sensitive(tuple[1]) }
}
