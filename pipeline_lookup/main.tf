data "aws_caller_identity" "this" {}

locals {
  result_suffix = "_lookup_results.jsonl"
}

#
# dbSNP lambda function
#
module "lambda-dbsnp" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "pgxflow-backend-dbsnp"
  description         = "Gets RSIDs for variants in a VCF"
  handler             = "lambda_function.lambda_handler"
  runtime             = "python3.12"
  memory_size         = 1792
  timeout             = 600
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-dbsnp.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/dbsnp"

  tags = var.common-tags

  environment_variables = {
    PGXFLOW_BUCKET           = var.pgxflow-backend-bucket-name
    DPORTAL_BUCKET           = var.data-portal-bucket-name
    REFERENCE_BUCKET         = var.pgxflow-reference-bucket-name
    PGXFLOW_LOOKUP_LAMBDA    = module.lambda-lookup.lambda_function_arn
    DBSNP_REFERENCE          = var.dbsnp_reference
    LOOKUP_REFERENCE         = var.lookup_configuration["assoc_matrix_filename"]
    CHR_HEADER               = var.lookup_configuration["chr_header"]
    START_HEADER             = var.lookup_configuration["start_header"]
    END_HEADER               = var.lookup_configuration["end_header"]
    DYNAMO_CLINIC_JOBS_TABLE = var.dynamo-clinic-jobs-table
    SEND_JOB_EMAIL_ARN       = var.send-job-email-lambda-function-arn
    HTS_S3_HOST              = "s3.${var.region}.amazonaws.com"
  }

  layers = [
    var.python_modules_layer,
    var.binaries_layer,
  ]
}

#
# lookup lambda function
#
module "lambda-lookup" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "pgxflow-backend-lookup"
  description         = "Performs a lookup on custom association matrix to retrieve annotations"
  handler             = "lambda_function.lambda_handler"
  runtime             = "python3.12"
  memory_size         = 1792
  timeout             = 600
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-lookup.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/lookup"

  tags = var.common-tags

  environment_variables = {
    RESULT_SUFFIX            = local.result_suffix
    PGXFLOW_BUCKET           = var.pgxflow-backend-bucket-name
    DPORTAL_BUCKET           = var.data-portal-bucket-name
    REFERENCE_BUCKET         = var.pgxflow-reference-bucket-name
    LOOKUP_REFERENCE         = var.lookup_configuration["assoc_matrix_filename"]
    CHR_HEADER               = var.lookup_configuration["chr_header"]
    START_HEADER             = var.lookup_configuration["start_header"]
    END_HEADER               = var.lookup_configuration["end_header"]
    PGXFLOW_GNOMAD_LAMBDA    = module.lambda-gnomad.lambda_function_arn
    DYNAMO_CLINIC_JOBS_TABLE = var.dynamo-clinic-jobs-table
    SEND_JOB_EMAIL_ARN       = var.send-job-email-lambda-function-arn
    HTS_S3_HOST              = "s3.${var.region}.amazonaws.com"
  }

  layers = [
    var.python_modules_layer,
    var.binaries_layer,
  ]
}

#
# gnomad lambda function
#
module "lambda-gnomad" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "pgxflow-backend-gnomad"
  description         = "Adds data from gnomAD to the lookup results"
  handler             = "lambda_function.lambda_handler"
  runtime             = "python3.12"
  memory_size         = 1792
  timeout             = 600
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-gnomad.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/gnomad"

  tags = var.common-tags

  environment_variables = {
    RESULT_SUFFIX            = local.result_suffix
    PGXFLOW_BUCKET           = var.pgxflow-backend-bucket-name
    DPORTAL_BUCKET           = var.data-portal-bucket-name
    DYNAMO_CLINIC_JOBS_TABLE = var.dynamo-clinic-jobs-table
    SEND_JOB_EMAIL_ARN       = var.send-job-email-lambda-function-arn
  }

  layers = [
    var.python_modules_layer,
    var.binaries_layer,
  ]
}

#
# updateReferenceFiles Lambda Function
#
module "lambda-updateReferenceFiles" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "pgxflow-backend-lookup-updateReferenceFiles"
  description         = "Updates the lookup reference files"
  handler             = "lambda_function.lambda_handler"
  runtime             = "python3.12"
  memory_size         = 1792
  timeout             = 28
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-updateReferenceFiles.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/updateReferenceFiles"

  tags = var.common-tags

  environment_variables = {
    REFERENCE_LOCATION              = var.pgxflow-reference-bucket-name
    DYNAMO_PGXFLOW_REFERENCES_TABLE = var.dynamo-references-table
    EC2_IAM_INSTANCE_PROFILE        = var.ec2-references-instance-profile
  }

  layers = [
    var.python_modules_layer,
  ]
}
