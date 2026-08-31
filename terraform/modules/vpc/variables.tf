variable "vpc_name" {
  description = "Name tag applied to the VPC and used as a prefix for all child resources."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC (e.g. 10.0.0.0/16)."
  type        = string
}

variable "az_count" {
  description = "Number of Availability Zones to deploy into. Must be 2 or 3."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count must be either 2 or 3."
  }
}

variable "cluster_name" {
  description = "Name of the EKS cluster. Used to tag subnets and the VPC so the cluster can discover them."
  type        = string
}

variable "tags" {
  description = "Map of tags to apply to all resources created by this module."
  type        = map(string)
  default     = {}
}
