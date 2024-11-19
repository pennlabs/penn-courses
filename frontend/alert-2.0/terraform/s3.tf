resource "aws_s3_bucket" "website" {
  bucket = "penncoursealert.com"
}

resource "aws_s3_object" "test" {
  for_each     = local.dist
  bucket       = aws_s3_bucket.website.bucket
  key          = each.key
  source       = each.value.source
  content_type = each.value.content_type
  etag         = filemd5(each.value.source)
}

resource "aws_s3_bucket_ownership_controls" "website" {
  bucket = aws_s3_bucket.website.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "website" {
  bucket = aws_s3_bucket.website.id
  acl    = "private"
}

resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website.bucket
  index_document {
    suffix = "index.html"
  }
  error_document {
    key = "index.html"
  }
}
