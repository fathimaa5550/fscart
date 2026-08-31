variable "aws_region" {
  description = "AWS region where all resources will be deployed."
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster. Also used as a prefix for related resources."
  type        = string
  default     = "fscart"
}

variable "kubernetes_version" {
  description = "Kubernetes version to use for the EKS cluster."
  type        = string
  default     = "1.30"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of Availability Zones to span (2 or 3)."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count must be 2 or 3."
  }
}

variable "node_groups" {
  description = <<-EOT
    Map of EKS managed node group configurations. Each key becomes the node
    group name. Supported attributes per group:
      instance_types  - list of EC2 instance types
      desired_size    - initial node count
      min_size        - minimum node count
      max_size        - maximum node count
      labels          - (optional) map of Kubernetes node labels
      taints          - (optional) list of taint objects {key, value, effect}
  EOT
  type        = map(any)
  default = {
    system = {
      instance_types = ["t3.medium"]
      desired_size   = 2
      min_size       = 1
      max_size       = 4
      labels = {
        role = "system"
      }
    }
  }
}

variable "tags" {
  description = "Additional tags applied to all taggable resources."
  type        = map(string)
  default = {
    Project     = "fscart"
    ManagedBy   = "terraform"
    Environment = "production"
  }
}
