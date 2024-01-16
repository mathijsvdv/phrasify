provider "aws" {
  region = local.region
}

locals {
  name   = "test-eks-cluster"
  region = "eu-central-1"

  vpc_cidr = "172.32.0.0/16"
  azs      = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]

  public_subnets  = ["172.32.1.0/24", "172.32.2.0/24", "172.32.3.0/24"]
  private_subnets = ["172.32.4.0/24", "172.32.5.0/24", "172.32.6.0/24"]
  intra_subnets   = ["172.32.7.0/24", "172.32.8.0/24", "172.32.9.0/24"]

  tags = {
    Example = local.name
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.1"

  name = local.name
  cidr = local.vpc_cidr

  azs             = local.azs
  private_subnets = local.private_subnets
  public_subnets  = local.public_subnets
  intra_subnets   = local.intra_subnets

  enable_nat_gateway = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}


module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "19.21.0"

  cluster_name                   = local.name
  cluster_endpoint_public_access = true

  cluster_addons = {
    coredns = {
      preserve    = true
      most_recent = true

      timeouts = {
        create = "25m"
        delete = "10m"
      }
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
  }

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.intra_subnets

  # EKS Managed Node Group(s)
  eks_managed_node_group_defaults = {
    ami_type       = "AL2_x86_64"
    instance_types = ["m5.large"]

    attach_cluster_primary_security_group = true
  }

  eks_managed_node_groups = {
    test-cluster-wg = {
      min_size     = 1
      max_size     = 2
      desired_size = 1

      instance_types = ["t3.large"]
      capacity_type  = "SPOT"

      tags = {
        ExtraTag = "hello-eks-managed-node-group"
      }
    }
  }

  tags = local.tags
}
