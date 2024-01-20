resource "null_resource" "ingresses" {
  triggers = {
    eks_context = aws_eks_cluster.cluster.arn
  }
  provisioner "local-exec" {
    when    = destroy
    command = "kubectl config use-context \"$EKS_CONTEXT\" && kubectl delete ing --all -A"
    environment = {
      EKS_CONTEXT = self.triggers.eks_context
    }
  }

  depends_on = [
    helm_release.aws-load-balancer-controller,
    kubernetes_deployment.external_dns
  ]
}
