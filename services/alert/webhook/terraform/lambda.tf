data "archive_file" "source" {
  type        = "zip"
  source_dir  = "${path.module}/../dist/build.lambda"
  output_path = "${path.module}/../dist/build.lambda.zip"
}

resource "aws_s3_object" "payload" {
  bucket     = "pennlabs-lambda-deployment"
  key        = "org_pennlabs_courses_alert_webhook/v0.7.0/${filesha1("${path.module}/../dist/build.lambda.zip")}.zip"
  source     = "${path.module}/../dist/build.lambda.zip"
  depends_on = [data.archive_file.source]
}

resource "aws_lambda_function" "courses_alert_webhook" {
  function_name = "org_pennlabs_courses_alert_webhook"
  s3_bucket     = aws_s3_object.payload.bucket
  s3_key        = aws_s3_object.payload.key
  handler       = "main.handler"
  runtime       = "nodejs20.x"
  role          = aws_iam_role.courses_alert_webhook_exec.arn
  logging_config {
    log_group  = aws_cloudwatch_log_group.courses_alert_webhook.name
    log_format = "Text"
  }
  environment {
    variables = local.envs
  }
}

resource "aws_cloudwatch_log_group" "courses_alert_webhook" {
  name = "/aws/lambda/org_pennlabs_courses_alert_webhook"
}

resource "aws_iam_role" "courses_alert_webhook_exec" {
  name = "org_pennlabs_courses_alert_webhook"
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
  name = "function-logging-policy"
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

resource "aws_iam_policy" "email" {
  name = "function-email-policy"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        Action : [
          "ses:SendEmail",
          "ses:SendRawEmail",
          "ses:SendTemplatedEmail"
        ],
        Effect : "Allow",
        Resource : "arn:aws:ses:us-east-1:449445102765:identity/penncoursealert.com"
      },
      {
        Action : [
          "ses:SendTemplatedEmail"
        ],
        Effect : "Allow",
        Resource : "arn:aws:ses:us-east-1:449445102765:template/PennCourseAlert"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "logging_policy_attachment" {
  role       = aws_iam_role.courses_alert_webhook_exec.id
  policy_arn = aws_iam_policy.logging.arn
}

resource "aws_iam_role_policy_attachment" "email_policy_attachment" {
  role       = aws_iam_role.courses_alert_webhook_exec.id
  policy_arn = aws_iam_policy.email.arn
}
