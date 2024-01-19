locals {
  kubernetes = {
    host                   = aws_eks_cluster.cluster.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.cluster.certificate_authority[0].data)
    exec = {
      api_version = "client.authentication.k8s.io/v1beta1"
      args        = ["eks", "get-token", "--cluster-name", aws_eks_cluster.cluster.id]
      command     = "aws"
    }
  }
}

provider "kubernetes" {
  host                   = local.kubernetes.host
  cluster_ca_certificate = local.kubernetes.cluster_ca_certificate
  exec {
    api_version = local.kubernetes.exec.api_version
    args        = local.kubernetes.exec.args
    command     = local.kubernetes.exec.command
  }
}

provider "helm" {
  kubernetes {
    host                   = local.kubernetes.host
    cluster_ca_certificate = local.kubernetes.cluster_ca_certificate
    exec {
      api_version = local.kubernetes.exec.api_version
      args        = local.kubernetes.exec.args
      command     = local.kubernetes.exec.command
    }
  }
}
