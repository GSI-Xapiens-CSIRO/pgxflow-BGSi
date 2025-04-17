# References Table 
resource "aws_dynamodb_table" "pgxflow_references" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  name         = "pgxflow-references"
  tags         = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }
}
