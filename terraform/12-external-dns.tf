data "aws_iam_policy_document" "external_dns_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:external-dns"]
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "external_dns" {
  assume_role_policy = data.aws_iam_policy_document.external_dns_assume_role_policy.json
  name               = "external-dns"
}

resource "aws_iam_policy" "external_dns" {
  policy = file("./policies/ExternalDNSAccess.json")
  name   = "ExternalDNSAccess"
}

resource "aws_iam_role_policy_attachment" "external_dns_attach" {
  role       = aws_iam_role.external_dns.name
  policy_arn = aws_iam_policy.external_dns.arn
}

resource "kubernetes_service_account" "external_dns" {
  metadata {
    name = "external-dns"
    namespace = "kube-system"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.external_dns.arn
    }
  }

  depends_on = [
    null_resource.full-eks-cluster,
    aws_iam_role_policy_attachment.external_dns_attach
  ]
}

resource "kubernetes_cluster_role" "external_dns" {

  metadata {
    name = "external-dns"
  }

  rule {
    api_groups = [""]
    resources = ["services", "endpoints", "pods"]
    verbs = ["get", "watch", "list"]
  }

  rule {
    api_groups = ["extensions", "networking.k8s.io"]
    resources = ["ingresses"]
    verbs = ["get", "watch", "list"]
  }

  rule {
    api_groups = [""]
    resources = ["nodes"]
    verbs = ["list", "watch"]
  }

  depends_on = [null_resource.full-eks-cluster]
}

resource "kubernetes_cluster_role_binding" "external_dns_viewer" {
  metadata {
    name = "external-dns-viewer"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind = "ClusterRole"
    name = kubernetes_cluster_role.external_dns.metadata[0].name
  }

  subject {
    kind = "ServiceAccount"
    name = kubernetes_service_account.external_dns.metadata[0].name
    namespace = kubernetes_service_account.external_dns.metadata[0].namespace
  }
}

resource "kubernetes_deployment" "external_dns" {
  metadata {
    name = "external-dns"
    namespace = "kube-system"
  }

  spec {
    strategy {
      type = "Recreate"
    }

    selector {
      match_labels = {
        app = "external-dns"
      }
    }

    template {
      metadata {
        labels = {
          app = "external-dns"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.external_dns.metadata[0].name
        container {
          name = "external-dns"
          image = "k8s.gcr.io/external-dns/external-dns:v0.12.0"
          args = [
            "--source=service",
            "--source=ingress",
            "--provider=aws",
            # "--policy=upsert-only",  # would prevent ExternalDNS from deleting any records, omit to enable full synchronization
            "--aws-zone-type=public",
            "--registry=txt",
            "--txt-owner-id=eks-phrasify"
          ]
          resources {
            requests = {
              cpu = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu = "500m"
              memory = "512Mi"
            }
          }
        }

        security_context {
          fs_group = 65534  # For ExternalDNS to be able to read Kubernetes and AWS token files
        }
      }
    }
  }

  depends_on = [
    kubernetes_cluster_role_binding.external_dns_viewer
  ]
}
