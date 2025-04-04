### binaries layer
# resource for the binraries layer
resource "archive_file" "binaries_layer" {
  type        = "zip"
  source_dir  = "${path.module}/layers/binaries/"
  output_path = "${path.module}/binaries.zip"

  depends_on = [null_resource.init_script]
}

# binaries layer definition
resource "aws_lambda_layer_version" "binaries_layer" {
  filename         = archive_file.binaries_layer.output_path
  layer_name       = "pgxflow_backend_binaries_layer"
  source_code_hash = archive_file.binaries_layer.output_base64sha256

  compatible_runtimes = ["python3.12"]
}

### python thirdparty libraries layer
# contains ijson
module "python_libraries_layer" {
  source = "terraform-aws-modules/lambda/aws"

  create_layer = true

  layer_name          = "pgxflow_backend_python_libraries_layer"
  description         = "python libraries"
  compatible_runtimes = ["python3.12"]

  source_path = "${path.module}/layers/python_libraries/"

  store_on_s3 = true
  s3_bucket   = aws_s3_bucket.lambda-layers-bucket.bucket

  depends_on = [null_resource.init_script]
}

### python first party modules layer
module "python_modules_layer" {
  source = "terraform-aws-modules/lambda/aws"

  create_layer = true

  layer_name          = "pgxflow_backend_python_modules_layer"
  description         = "python modules"
  compatible_runtimes = ["python3.12"]

  source_path = "${path.module}/shared_resources/python-modules/"

  store_on_s3 = true
  s3_bucket   = aws_s3_bucket.lambda-layers-bucket.bucket
}
