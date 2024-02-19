resource "kubernetes_storage_class" "efs" {
  metadata {
    name = "efs-sc"
  }
  storage_provisioner = "efs.csi.aws.com"
  parameters = {
    provisioningMode = "efs-ap"
    fileSystemId = aws_efs_file_system.eks.id
    directoryPerms = "700"
  }

  depends_on = [aws_eks_addon.efs_csi_driver]
}
