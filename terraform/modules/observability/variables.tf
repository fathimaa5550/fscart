###############################################################################
# fscart – Observability Module Variables
###############################################################################

variable "cluster_name" {
  description = "Name of the EKS/Kubernetes cluster where the observability stack is deployed."
  type        = string
}

variable "grafana_admin_password" {
  description = "Admin password for the Grafana dashboard. Store this value in AWS Secrets Manager or similar and pass it in; never commit in plaintext."
  type        = string
  sensitive   = true
  default     = "admin"
}

variable "tags" {
  description = "A map of tags to apply to all taggable resources created by this module."
  type        = map(string)
  default     = {}
}
