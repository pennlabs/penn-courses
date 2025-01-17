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

data "aws_route53_zone" "penncoursealert" {
  name         = "penncoursealert.com."
  private_zone = false
}

# output "prod-url" {
#   value = aws_api_gateway_stage.production.invoke_url
# }

output "staging-url" {
  value = aws_api_gateway_stage.staging.invoke_url
}

locals {
  envs = { for tuple in regexall("(.*)=(.*)", file("deploy.env")) : tuple[0] => sensitive(tuple[1]) }
}
