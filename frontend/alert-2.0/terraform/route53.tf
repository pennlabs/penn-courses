
resource "aws_route53_record" "website" {
  zone_id = data.aws_route53_zone.penncoursealert.id
  name    = "staging.penncoursealert.com"
  type    = "CNAME"
  ttl     = 300
  records = ["${aws_cloudfront_distribution.website.domain_name}"]
}
