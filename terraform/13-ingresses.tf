resource "null_resource" "ingresses" {
  /*
  This resource is used to trigger the deletion of all ingresses
  when the cluster is destroyed. This is necessary because the
  ingress controller and external-dns resources are not managed
  by Terraform. Namely:
  - The AWS Load Balancer Controller creates a load balancer for each ingress. Upon
    deletion of the ingress, the load balancer is deleted automatically, but only
    if the AWS Load Balancer Controller is present. This resource ensures that the
    ingresses are deleted before the AWS Load Balancer Controller is destroyed, so
    it can handle the deletion of the load balancers.
  - External DNS creates DNS records for each ingress. Upon deletion of the ingress,
    the DNS records are deleted automatically, but only if the External DNS is present.
    With this resource, we can ensure that the DNS records are deleted when the
    cluster is destroyed.
  */
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
