terraform {
  required_version = "1.8.4"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.74.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

data "aws_route53_zone" "penncoursealert" {
  name         = "penncoursealert.com."
  private_zone = false
}

locals {
  mime_type_map = {
    "html" = "text/html"
    "css"  = "text/css"
    "js"   = "application/javascript"
    "json" = "application/json"
    "png"  = "image/png"
    "jpg"  = "image/jpeg"
    "jpeg" = "image/jpeg"
    "gif"  = "image/gif"
    "svg"  = "image/svg+xml"
    "ico"  = "image/x-icon"
    "pdf"  = "application/pdf"
    "txt"  = "text/plain"
    "xml"  = "application/xml"
    "mp4"  = "video/mp4"
    "webm" = "video/webm"
    "ogg"  = "video/ogg"
    "mp3"  = "audio/mpeg"
    "wav"  = "audio/wav"
    "flac" = "audio/flac"
  }
  dist = {
    for file in fileset(path.module, "../dist/**/*") :
    replace(file, "../dist/", "") => {
      source       = file
      content_type = lookup(local.mime_type_map, regex(".+\\.(.+)$", file)[0], "application/octet-stream")
    }
  }
}
