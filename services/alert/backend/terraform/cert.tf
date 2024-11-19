resource "aws_acm_certificate" "staging" {
  domain_name       = "api.staging.penncoursealert.com"
  validation_method = "DNS"
}

resource "aws_route53_record" "staging_cert" {
  for_each = {
    for dvo in aws_acm_certificate.staging.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.penncoursealert.id
}

resource "aws_acm_certificate_validation" "website" {
  certificate_arn         = aws_acm_certificate.staging.arn
  validation_record_fqdns = [for record in aws_route53_record.staging_cert : record.fqdn]
}
