# ---------------------------------------------------------------------------
# fscart — EKS infrastructure root module
# ---------------------------------------------------------------------------

# Fetch an authentication token for the EKS cluster so that the Kubernetes,
# Helm, and kubectl providers can authenticate. This data source depends on
# the EKS cluster being created first.
data "aws_eks_cluster_auth" "this" {
  name = module.eks.cluster_name
}

# ---------------------------------------------------------------------------
# VPC
# ---------------------------------------------------------------------------
module "vpc" {
  source = "./modules/vpc"

  vpc_name     = var.cluster_name
  vpc_cidr     = var.vpc_cidr
  az_count     = var.az_count
  cluster_name = var.cluster_name
  tags         = var.tags
}

# ---------------------------------------------------------------------------
# EKS Cluster
# ---------------------------------------------------------------------------
module "eks" {
  source = "./modules/eks"

  cluster_name       = var.cluster_name
  kubernetes_version = var.kubernetes_version

  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids

  node_groups = var.node_groups
  tags        = var.tags
}
