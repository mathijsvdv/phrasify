data "aws_iam_policy_document" "efs_csi_driver_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringLike"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:efs-csi-*"]
    }

    condition {
      test     = "StringLike"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "efs_csi_driver" {
  assume_role_policy = data.aws_iam_policy_document.efs_csi_driver_assume_role_policy.json
  name               = "eks-efs-csi-driver"
}

resource "aws_iam_role_policy_attachment" "efs_csi_driver_attach" {
  role       = aws_iam_role.efs_csi_driver.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEFSCSIDriverPolicy"
}


resource "aws_eks_addon" "efs_csi_driver" {
  cluster_name                = aws_eks_cluster.cluster.name
  addon_name                  = "aws-efs-csi-driver"
  addon_version               = "v1.7.4-eksbuild.1"
  resolve_conflicts_on_update = "PRESERVE"
  service_account_role_arn    = aws_iam_role.efs_csi_driver.arn
}
