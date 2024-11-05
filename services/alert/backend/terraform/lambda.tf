data "archive_file" "source" {
  type        = "zip"
  source_dir  = "${path.module}/../dist/build.lambda"
  output_path = "${path.module}/../dist/build.lambda.zip"
}

resource "aws_s3_object" "payload" {
  bucket     = "pennlabs-lambda-deployment"
  key        = "org_pennlabs_courses_alert_backend/v0.7.0/${data.archive_file.source.output_sha256}.zip"
  source     = "${path.module}/../dist/build.lambda.zip"
  depends_on = [data.archive_file.source]
}


resource "aws_lambda_function" "courses_alert_backend" {
  function_name = "org_pennlabs_courses_alert_backend"
  s3_bucket     = aws_s3_object.payload.bucket
  s3_key        = aws_s3_object.payload.key
  handler       = "main.fetch"
  runtime       = "provided.al2"
  architectures = ["arm64"]
  role          = aws_iam_role.courses_alert_backend_exec.arn
  layers = [
    # TODO: in future, we should include bun in this terrafrom file
    "arn:aws:lambda:us-east-1:449445102765:layer:bun:1"
  ]
  logging_config {
    log_group  = aws_cloudwatch_log_group.courses_alert_backend.name
    log_format = "Text"
  }
  environment {
    variables = local.envs
  }
}

resource "aws_cloudwatch_log_group" "courses_alert_backend" {
  name = "/aws/lambda/org_pennlabs_courses_alert_backend"
}

resource "aws_iam_role" "courses_alert_backend_exec" {
  name = "org_pennlabs_courses_alert_backend"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "logging" {
  name = "org_pennlabs_courses_alert_backend_logging_policy"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        Action : [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect : "Allow",
        Resource : "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "logging_policy_attachment" {
  role       = aws_iam_role.courses_alert_backend_exec.name
  policy_arn = aws_iam_policy.logging.arn
}
