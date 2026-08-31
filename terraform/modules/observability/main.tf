###############################################################################
# fscart – Observability Module
# Installs: Istio, Kiali, Prometheus, Loki, Tempo, Grafana, Promtail
###############################################################################

terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.13.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.29.0"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.14.0"
    }
  }
}

###############################################################################
# Namespaces
###############################################################################

resource "kubernetes_namespace" "istio_system" {
  metadata {
    name = "istio-system"
    labels = {
      "istio-injection" = "disabled"
    }
  }
}

resource "kubernetes_namespace" "istio_ingress" {
  metadata {
    name = "istio-ingress"
    labels = {
      "istio-injection" = "enabled"
    }
  }
}

resource "kubernetes_namespace" "kiali_operator" {
  metadata {
    name = "kiali-operator"
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    labels = {
      "istio-injection" = "enabled"
    }
  }
}

###############################################################################
# Istio – base CRDs
###############################################################################

resource "helm_release" "istio_base" {
  name             = "istio-base"
  repository       = "https://istio-release.storage.googleapis.com/charts"
  chart            = "base"
  version          = "1.21.0"
  namespace        = kubernetes_namespace.istio_system.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 300

  set {
    name  = "defaultRevision"
    value = "default"
  }

  depends_on = [kubernetes_namespace.istio_system]
}

###############################################################################
# Istio – control plane (istiod)
###############################################################################

resource "helm_release" "istiod" {
  name             = "istiod"
  repository       = "https://istio-release.storage.googleapis.com/charts"
  chart            = "istiod"
  version          = "1.21.0"
  namespace        = kubernetes_namespace.istio_system.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 300

  set {
    name  = "telemetry.enabled"
    value = "true"
  }

  set {
    name  = "pilot.traceSampling"
    value = "100"
  }

  # Enable Prometheus metrics scraping
  set {
    name  = "meshConfig.enablePrometheusMerge"
    value = "true"
  }

  # Default tracing provider (Tempo via OTLP)
  set {
    name  = "meshConfig.defaultConfig.tracing.zipkin.address"
    value = "tempo.monitoring.svc.cluster.local:9411"
  }

  depends_on = [helm_release.istio_base]
}

###############################################################################
# Istio – ingress gateway
###############################################################################

resource "helm_release" "istio_ingress" {
  name             = "istio-ingress"
  repository       = "https://istio-release.storage.googleapis.com/charts"
  chart            = "gateway"
  version          = "1.21.0"
  namespace        = kubernetes_namespace.istio_ingress.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 300

  set {
    name  = "service.type"
    value = "LoadBalancer"
  }

  set {
    name  = "labels.app"
    value = "istio-ingressgateway"
  }

  set {
    name  = "labels.istio"
    value = "ingressgateway"
  }

  depends_on = [helm_release.istiod]
}

###############################################################################
# Prometheus (kube-prometheus-stack) – required by Kiali
###############################################################################

resource "helm_release" "prometheus" {
  name             = "prometheus"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  namespace        = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 600

  # Disable standalone Grafana; we manage it separately
  set {
    name  = "grafana.enabled"
    value = "false"
  }

  # Scrape Istio control-plane metrics
  set {
    name  = "prometheus.prometheusSpec.additionalScrapeConfigsSecret.enabled"
    value = "false"
  }

  set {
    name  = "prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues"
    value = "false"
  }

  set {
    name  = "prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues"
    value = "false"
  }

  set {
    name  = "prometheus.prometheusSpec.ruleSelectorNilUsesHelmValues"
    value = "false"
  }

  # Persistence for Prometheus
  set {
    name  = "prometheus.prometheusSpec.retention"
    value = "15d"
  }

  set {
    name  = "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.accessModes[0]"
    value = "ReadWriteOnce"
  }

  set {
    name  = "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage"
    value = "20Gi"
  }

  # AlertManager
  set {
    name  = "alertmanager.enabled"
    value = "true"
  }

  depends_on = [kubernetes_namespace.monitoring]
}

###############################################################################
# Kiali – operator
###############################################################################

resource "helm_release" "kiali_operator" {
  name             = "kiali-operator"
  repository       = "https://kiali.org/helm-charts"
  chart            = "kiali-operator"
  namespace        = kubernetes_namespace.kiali_operator.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 300

  set {
    name  = "watchNamespace"
    value = ""
  }

  set {
    name  = "clusterRoleCreator"
    value = "true"
  }

  depends_on = [
    helm_release.istiod,
    helm_release.prometheus,
    kubernetes_namespace.kiali_operator,
  ]
}

###############################################################################
# Kiali – Custom Resource (CR)
# Points at Prometheus, Grafana, and Tempo for service mesh observability
###############################################################################

resource "kubectl_manifest" "kiali_cr" {
  yaml_body = templatefile("${path.module}/../../../observability/kiali-cr.yaml", {
    grafana_url    = "http://grafana.monitoring.svc.cluster.local:80"
    prometheus_url = "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090"
    tempo_url      = "http://tempo.monitoring.svc.cluster.local:16686"
  })

  depends_on = [helm_release.kiali_operator]
}

###############################################################################
# Loki – log aggregation (single-binary, filesystem storage)
###############################################################################

resource "helm_release" "loki" {
  name             = "loki"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "loki"
  version          = "6.6.2"
  namespace        = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 300

  values = [
    file("${path.module}/../../../observability/loki-values.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

###############################################################################
# Tempo – distributed tracing (local storage)
###############################################################################

resource "helm_release" "tempo" {
  name             = "tempo"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "tempo"
  version          = "1.10.1"
  namespace        = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 300

  values = [
    file("${path.module}/../../../observability/tempo-values.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

###############################################################################
# Grafana – standalone dashboard
###############################################################################

resource "helm_release" "grafana" {
  name             = "grafana"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "grafana"
  version          = "8.0.0"
  namespace        = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 300

  values = [
    file("${path.module}/../../../observability/grafana-values.yaml")
  ]

  set_sensitive {
    name  = "adminPassword"
    value = var.grafana_admin_password
  }

  depends_on = [
    helm_release.prometheus,
    helm_release.loki,
    helm_release.tempo,
  ]
}

###############################################################################
# Promtail – log shipper → Loki
###############################################################################

resource "helm_release" "promtail" {
  name             = "promtail"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "promtail"
  namespace        = kubernetes_namespace.monitoring.metadata[0].name
  create_namespace = false
  wait             = true
  timeout          = 300

  set {
    name  = "config.clients[0].url"
    value = "http://loki.monitoring.svc.cluster.local:3100/loki/api/v1/push"
  }

  # Scrape all pods across all namespaces
  set {
    name  = "config.snippets.extraScrapeConfigs"
    value = ""
  }

  # Resource limits
  set {
    name  = "resources.limits.cpu"
    value = "200m"
  }

  set {
    name  = "resources.limits.memory"
    value = "128Mi"
  }

  set {
    name  = "resources.requests.cpu"
    value = "100m"
  }

  set {
    name  = "resources.requests.memory"
    value = "64Mi"
  }

  # Tolerations so Promtail runs on every node (including control-plane taints)
  set {
    name  = "tolerations[0].key"
    value = "node-role.kubernetes.io/control-plane"
  }

  set {
    name  = "tolerations[0].operator"
    value = "Exists"
  }

  set {
    name  = "tolerations[0].effect"
    value = "NoSchedule"
  }

  depends_on = [helm_release.loki]
}
