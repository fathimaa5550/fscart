###############################################################################
# fscart – Observability Module Outputs
###############################################################################

output "grafana_service" {
  description = "Kubernetes service name for Grafana in the monitoring namespace."
  value       = "grafana.${helm_release.grafana.namespace}.svc.cluster.local:80"
}

output "kiali_service" {
  description = "Kubernetes service name for the Kiali server in the istio-system namespace."
  value       = "kiali.istio-system.svc.cluster.local:20001"
}

output "loki_service" {
  description = "Kubernetes service name for Loki in the monitoring namespace."
  value       = "loki.${helm_release.loki.namespace}.svc.cluster.local:3100"
}

output "tempo_service" {
  description = "Kubernetes service name for Tempo in the monitoring namespace (OTLP gRPC :4317, HTTP :4318, Zipkin :9411)."
  value       = "tempo.${helm_release.tempo.namespace}.svc.cluster.local"
}

output "prometheus_service" {
  description = "Kubernetes service name for the Prometheus server in the monitoring namespace."
  value       = "prometheus-kube-prometheus-prometheus.${helm_release.prometheus.namespace}.svc.cluster.local:9090"
}

output "istio_ingress_namespace" {
  description = "Namespace where the Istio ingress gateway is deployed."
  value       = helm_release.istio_ingress.namespace
}

output "grafana_helm_status" {
  description = "Helm release status for Grafana."
  value       = helm_release.grafana.status
}

output "loki_helm_status" {
  description = "Helm release status for Loki."
  value       = helm_release.loki.status
}

output "tempo_helm_status" {
  description = "Helm release status for Tempo."
  value       = helm_release.tempo.status
}
