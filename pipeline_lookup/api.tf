#
# /pipeline_lookup
#
resource "aws_api_gateway_resource" "pipeline_lookup" {
  rest_api_id = var.pgxflow-api-gateway-id
  parent_id   = var.pgxflow-api-gateway-root-resource-id
  path_part   = "pipeline_lookup"
}

# 
# /pipeline_lookup/submit
# 
resource "aws_api_gateway_resource" "submit" {
  rest_api_id = var.pgxflow-api-gateway-id
  parent_id   = aws_api_gateway_resource.pipeline_lookup.id
  path_part   = "submit"
}

resource "aws_api_gateway_method" "submit-options" {
  rest_api_id   = var.pgxflow-api-gateway-id
  resource_id   = aws_api_gateway_resource.submit.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "submit-options" {
  rest_api_id = aws_api_gateway_method.submit-options.rest_api_id
  resource_id = aws_api_gateway_method.submit-options.resource_id
  http_method = aws_api_gateway_method.submit-options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-options" {
  rest_api_id = aws_api_gateway_method.submit-options.rest_api_id
  resource_id = aws_api_gateway_method.submit-options.resource_id
  http_method = aws_api_gateway_method.submit-options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "submit-options" {
  rest_api_id = aws_api_gateway_method.submit-options.rest_api_id
  resource_id = aws_api_gateway_method.submit-options.resource_id
  http_method = aws_api_gateway_method.submit-options.http_method
  status_code = aws_api_gateway_method_response.submit-options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,PATCH,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-options]
}

resource "aws_api_gateway_method" "submit-patch" {
  rest_api_id   = var.pgxflow-api-gateway-id
  resource_id   = aws_api_gateway_resource.submit.id
  http_method   = "PATCH"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.pgxflow-user-pool-authorizer-id
}

resource "aws_api_gateway_method_response" "submit-patch" {
  rest_api_id = aws_api_gateway_method.submit-patch.rest_api_id
  resource_id = aws_api_gateway_method.submit-patch.resource_id
  http_method = aws_api_gateway_method.submit-patch.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-patch" {
  rest_api_id             = aws_api_gateway_method.submit-patch.rest_api_id
  resource_id             = aws_api_gateway_method.submit-patch.resource_id
  http_method             = aws_api_gateway_method.submit-patch.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-initLookup.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "submit-patch" {
  rest_api_id = aws_api_gateway_method.submit-patch.rest_api_id
  resource_id = aws_api_gateway_method.submit-patch.resource_id
  http_method = aws_api_gateway_method.submit-patch.http_method
  status_code = aws_api_gateway_method_response.submit-patch.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-patch]
}

resource "aws_api_gateway_method" "submit-post" {
  rest_api_id   = var.pgxflow-api-gateway-id
  resource_id   = aws_api_gateway_resource.submit.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.pgxflow-user-pool-authorizer-id
}

resource "aws_api_gateway_method_response" "submit-post" {
  rest_api_id = aws_api_gateway_method.submit-post.rest_api_id
  resource_id = aws_api_gateway_method.submit-post.resource_id
  http_method = aws_api_gateway_method.submit-post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-post" {
  rest_api_id             = aws_api_gateway_method.submit-post.rest_api_id
  resource_id             = aws_api_gateway_method.submit-post.resource_id
  http_method             = aws_api_gateway_method.submit-post.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-initLookup.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "submit-post" {
  rest_api_id = aws_api_gateway_method.submit-post.rest_api_id
  resource_id = aws_api_gateway_method.submit-post.resource_id
  http_method = aws_api_gateway_method.submit-post.http_method
  status_code = aws_api_gateway_method_response.submit-post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-post]
}

# permit lambda invocation
resource "aws_lambda_permission" "APIInitLookup" {
  statement_id  = "AllowAPIInitLookupInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-initLookup.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.pgxflow-api-gateway-execution-arn}/*/*/${aws_api_gateway_resource.submit.path_part}"
}

#
# /pipeline_lookup/results
#
resource "aws_api_gateway_resource" "results" {
  rest_api_id = var.pgxflow-api-gateway-id
  parent_id   = aws_api_gateway_resource.pipeline_lookup.id
  path_part   = "results"
}

resource "aws_api_gateway_method" "results-options" {
  rest_api_id   = var.pgxflow-api-gateway-id
  resource_id   = aws_api_gateway_resource.results.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "results-options" {
  rest_api_id = aws_api_gateway_method.results-options.rest_api_id
  resource_id = aws_api_gateway_method.results-options.resource_id
  http_method = aws_api_gateway_method.results-options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "results-options" {
  rest_api_id = aws_api_gateway_method.results-options.rest_api_id
  resource_id = aws_api_gateway_method.results-options.resource_id
  http_method = aws_api_gateway_method.results-options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "results-options" {
  rest_api_id = aws_api_gateway_method.results-options.rest_api_id
  resource_id = aws_api_gateway_method.results-options.resource_id
  http_method = aws_api_gateway_method.results-options.http_method
  status_code = aws_api_gateway_method_response.results-options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.results-options]
}

resource "aws_api_gateway_method" "results-get" {
  rest_api_id   = var.pgxflow-api-gateway-id
  resource_id   = aws_api_gateway_resource.results.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.pgxflow-user-pool-authorizer-id
}

resource "aws_api_gateway_method_response" "results-get" {
  rest_api_id = aws_api_gateway_method.results-get.rest_api_id
  resource_id = aws_api_gateway_method.results-get.resource_id
  http_method = aws_api_gateway_method.results-get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "results-get" {
  rest_api_id             = aws_api_gateway_method.results-get.rest_api_id
  resource_id             = aws_api_gateway_method.results-get.resource_id
  http_method             = aws_api_gateway_method.results-get.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getResultsURL.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "results-get" {
  rest_api_id = aws_api_gateway_method.results-get.rest_api_id
  resource_id = aws_api_gateway_method.results-get.resource_id
  http_method = aws_api_gateway_method.results-get.http_method
  status_code = aws_api_gateway_method_response.results-get.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.results-get]
}

# permit lambda invocation
resource "aws_lambda_permission" "APIGetResultsURL" {
  statement_id  = "AllowAPIGetResultsURLInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getResultsURL.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.pgxflow-api-gateway-execution-arn}/*/*/${aws_api_gateway_resource.results.path_part}"
}
