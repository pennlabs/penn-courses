resource "aws_route53_record" "staging" {
  name    = aws_api_gateway_domain_name.staging.domain_name
  type    = "A"
  zone_id = data.aws_route53_zone.penncoursealert.id
  alias {
    name                   = aws_api_gateway_domain_name.staging.regional_domain_name
    zone_id                = aws_api_gateway_domain_name.staging.regional_zone_id
    evaluate_target_health = false
  }
}
