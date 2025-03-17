output "api_url" {
  value       = "https://${aws_cloudfront_distribution.api_distribution.domain_name}/${aws_api_gateway_stage.PgxApi.stage_name}/"
  description = "URL used to invoke the API."
}
