variable "cluster_name" {
  description = "Name of the EKS cluster."
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS control plane."
  type        = string
  default     = "1.30"
}

variable "vpc_id" {
  description = "ID of the VPC in which the cluster will be created."
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for EKS nodes and the cluster endpoint."
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs. Used for public-facing load balancers."
  type        = list(string)
}

variable "endpoint_private_access" {
  description = "Whether the EKS API server endpoint is accessible from within the VPC."
  type        = bool
  default     = true
}

variable "endpoint_public_access" {
  description = "Whether the EKS API server endpoint is accessible from the internet."
  type        = bool
  default     = true
}

variable "public_access_cidrs" {
  description = "List of CIDR blocks allowed to access the public API server endpoint."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "cluster_log_types" {
  description = "EKS control-plane log types to enable in CloudWatch."
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
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
  default     = {}
}

variable "tags" {
  description = "Map of tags applied to all resources created by this module."
  type        = map(string)
  default     = {}
}
