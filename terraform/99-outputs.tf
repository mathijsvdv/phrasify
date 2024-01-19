output "aws_load_balancer_controller_role_arn" {
  value = aws_iam_role.aws_load_balancer_controller.arn
}

output "external_dns_role_arn" {
  value = aws_iam_role.external_dns.arn
}
