data "aws_iam_policy_document" "lambda-preprocessor" {
  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      var.data-portal-bucket-arn,
      var.pgxflow-reference-bucket-arn,
    ]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "projects/*/project-files/*",
      ]
    }
  }
  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${var.data-portal-bucket-arn}/projects/*/project-files/*",
      "${var.pgxflow-reference-bucket-arn}/*",
    ]
  }
  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${var.pgxflow-backend-bucket-arn}/*",
    ]
  }
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }
  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      module.lambda-pharmcat.lambda_function_arn,
      var.send-job-email-lambda-function-arn,
    ]
  }
}

data "aws_iam_policy_document" "lambda-pharmcat" {
  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      var.pgxflow-backend-bucket-arn,
    ]
  }
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${var.pgxflow-backend-bucket-arn}/*"
    ]
  }
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }
  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      module.lambda-postprocessor.lambda_function_arn,
      var.send-job-email-lambda-function-arn,
    ]
  }
}

data "aws_iam_policy_document" "lambda-postprocessor" {
  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      var.pgxflow-backend-bucket-arn,
      var.data-portal-bucket-arn,
    ]
  }
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${var.pgxflow-backend-bucket-arn}/*"
    ]
  }
  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${var.data-portal-bucket-arn}/projects/*/project-files/*"
    ]
  }
  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      module.lambda-gnomad.lambda_function_arn,
      var.send-job-email-lambda-function-arn,
    ]
  }
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }
}

data "aws_iam_policy_document" "lambda-gnomad" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${var.pgxflow-backend-bucket-arn}/*"
    ]
  }
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }
  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${var.data-portal-bucket-arn}/projects/*/clinical-workflows/*"
    ]
  }
  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.send-job-email-lambda-function-arn,
    ]
  }
}

#
# updateReferenceFiles Lambda Function
#
data "aws_iam_policy_document" "lambda-updateReferenceFiles" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${var.pgxflow-reference-bucket-arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      var.pgxflow-reference-bucket-arn,
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DescribeTable",
    ]
    resources = [
      var.dynamo-references-table-arn
    ]
  }
  statement {
    actions = [
      "ec2:RunInstances",
      "ec2:DescribeInstances",
      "ec2:CreateTags",
      "ec2:DescribeImages",
    ]
    resources = [
      "*",
    ]
  }

  statement {
    actions = [
      "iam:PassRole",
    ]
    resources = [
      var.ec2-references-instance-role-arn,
    ]
  }
}
