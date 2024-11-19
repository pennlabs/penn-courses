resource "aws_api_gateway_rest_api" "backend" {
  name        = "org_pennlabs_courses_alert_backend"
  description = "Penn Course Alert Backend API"
}

resource "aws_api_gateway_resource" "backend" {
  rest_api_id = aws_api_gateway_rest_api.backend.id
  parent_id   = aws_api_gateway_rest_api.backend.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "backend" {
  rest_api_id   = aws_api_gateway_rest_api.backend.id
  resource_id   = aws_api_gateway_rest_api.backend.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_deployment" "staging" {
  depends_on  = [aws_api_gateway_integration.backend]
  rest_api_id = aws_api_gateway_rest_api.backend.id
  stage_name  = "staging"
}

resource "aws_api_gateway_stage" "staging" {
  rest_api_id   = aws_api_gateway_rest_api.backend.id
  stage_name    = "staging"
  deployment_id = aws_api_gateway_deployment.staging.id
}

resource "aws_api_gateway_integration" "backend" {
  rest_api_id             = aws_api_gateway_rest_api.backend.id
  resource_id             = aws_api_gateway_method.backend.resource_id
  http_method             = aws_api_gateway_method.backend.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.courses_alert_backend.invoke_arn
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.courses_alert_backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.backend.execution_arn}/*/*"
}

resource "aws_api_gateway_domain_name" "staging" {
  domain_name              = "api.staging.penncoursealert.com"
  regional_certificate_arn = aws_acm_certificate.staging.arn
  security_policy          = "TLS_1_2"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_base_path_mapping" "staging" {
  api_id      = aws_api_gateway_rest_api.backend.id
  stage_name  = aws_api_gateway_stage.staging.stage_name
  domain_name = aws_api_gateway_domain_name.staging.domain_name
}
