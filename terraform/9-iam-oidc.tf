data "tls_certificate" "eks" {
  url = aws_eks_cluster.cluster.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.cluster.identity[0].oidc[0].issuer
}

resource "null_resource" "full-eks-cluster" {
  depends_on = [
    aws_nat_gateway.nat,
    null_resource.full-route-table,
    aws_eks_cluster.cluster,
    aws_eks_node_group.private-nodes,
    aws_iam_openid_connect_provider.eks
  ]
}
