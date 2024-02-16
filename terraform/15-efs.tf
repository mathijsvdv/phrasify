resource "aws_efs_file_system" "eks" {
  creation_token = "eks"

  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"
  encrypted        = true

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  tags = {
    Name = "eks"
  }
}

resource "aws_efs_mount_target" "a" {
  file_system_id  = aws_efs_file_system.eks.id
  subnet_id       = aws_subnet.private-eu-central-1a.id
  security_groups = [aws_eks_cluster.cluster.vpc_config[0].cluster_security_group_id]
}

resource "aws_efs_mount_target" "b" {
  file_system_id  = aws_efs_file_system.eks.id
  subnet_id       = aws_subnet.private-eu-central-1b.id
  security_groups = [aws_eks_cluster.cluster.vpc_config[0].cluster_security_group_id]
}

resource "aws_efs_mount_target" "c" {
  file_system_id  = aws_efs_file_system.eks.id
  subnet_id       = aws_subnet.private-eu-central-1c.id
  security_groups = [aws_eks_cluster.cluster.vpc_config[0].cluster_security_group_id]
}
