# Observability Stack Guide

Deployment, verification, and usage guide for the observability stack on Red Hat AI Enterprise.

## Table of Contents

- [Components](#components)
- [Installation](#installation)
- [Verification](#verification)
- [Usage](#usage)
- [Monitoring AI Workloads](#monitoring-ai-workloads)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## Components

**Operators:**
- Cluster Observability, Grafana, OpenTelemetry, Logging (cluster-logging), Loki

**Resources:**
- LokiStack (log storage) + MinIO backend
- Grafana (dashboards)
- OpenTelemetry Collector (tracing)
- User Workload Monitoring (Prometheus metrics)
- MLflow (experiment tracking)

## Installation

### Automated Install

```bash
cd deploy/helm/observability
chmod +x install-operators.sh deploy.sh

# Step 1: Install operators (2-3 minutes)
./install-operators.sh

# Step 2: Deploy resources (3-5 minutes)
./deploy.sh
```

### Manual Install

If you need to customize individual components:

```bash
cd deploy/helm/observability/helm

# Install operators
helm install cluster-obs cluster-observability-operator/
helm install grafana-op grafana-operator/
helm install otel-op otel-operator/
helm install logging-op logging-operator/

# Wait for CRDs
oc get crd opentelemetrycollectors.opentelemetry.io
oc get crd grafanas.grafana.integreatly.org
oc get crd lokistacks.loki.grafana.com

# Deploy resources
helm install otel-collector otel-collector/ -n observability-hub
helm install uwm uwm/
helm install grafana grafana/ -n observability-hub
helm install logging-stack logging-stack/ -n openshift-logging
helm install mlflow mlflow/ -n observability-hub
```

## Verification

**Check operators:**
```bash
oc get csv -A | grep -E "cluster-logging|loki-operator|grafana-operator|opentelemetry-operator|cluster-observability"
```

**Check pods:**
```bash
# Observability hub
oc get pods -n observability-hub

# Logging stack
oc get pods -n openshift-logging
```

**Verify LokiStack:**
```bash
oc get lokistack logging-loki -n openshift-logging
```

## Usage

### OpenShift Console Logging

Navigate to **Observe → Logs** in the OpenShift Console.

**Useful queries:**
```logql
# All logs from AI-Q namespace
{kubernetes_namespace_name="ns-aiq"}

# AI-Q backend logs
{kubernetes_namespace_name="ns-aiq", kubernetes_pod_name=~"aiq-backend.*"}

# vLLM model server logs
{kubernetes_namespace_name="ns-aiq", kubernetes_pod_name=~".*-predictor.*"}

# Filter for errors
{kubernetes_namespace_name="ns-aiq"} |~ "(?i)(error|exception|fail)"
```

### Grafana

**Get Grafana URL:**
```bash
echo "https://$(oc get route grafana-route -n observability-hub -o jsonpath='{.spec.host}')"
```

**Credentials:**
Check `deploy/helm/observability/helm/grafana/values.yaml` for configured credentials.

**Features:**
- Pre-configured vLLM metrics dashboard
- Query Prometheus metrics from User Workload Monitoring
- Create custom dashboards for AI workloads

### MLflow

**Get MLflow URL:**
```bash
echo "https://$(oc get route mlflow -n observability-hub -o jsonpath='{.spec.host}')"
```

**Use cases:**
- Track ML experiments
- Log model parameters, metrics, and artifacts
- Compare experiment runs
- Register and version models

## Troubleshooting

### Logs Not Appearing

**Check collector pods:**
```bash
oc get pods -n openshift-logging -l component=collector
oc logs -n openshift-logging -l component=collector --tail=50
```

**Check LokiStack:**
```bash
oc describe lokistack logging-loki -n openshift-logging
```

### LokiStack Not Ready

**Check MinIO:**
```bash
oc get pods -n openshift-logging -l app=minio
oc logs -n openshift-logging -l app=minio
```

**Verify bucket creation:**
```bash
oc get jobs -n openshift-logging
oc rsh -n openshift-logging $(oc get pod -l app=minio -o name -n openshift-logging) ls -la /data/loki
```

### Grafana Not Accessible

**Check Grafana pod:**
```bash
oc get pods -n observability-hub -l app=grafana
oc logs -n observability-hub deployment/grafana-deployment
```

**Check route:**
```bash
oc get route grafana-route -n observability-hub
```

### MLflow Connection Issues

**Check deployment:**
```bash
oc get deployment mlflow -n observability-hub
oc logs -n observability-hub deployment/mlflow
```

**Verify MLflow tracking token:**
If traces or experiments are not appearing in MLflow from the AI-Q application, verify that the `Authorization: "Bearer {YOUR_TOKEN_HERE}"` header in `deploy/helm/aiq-rh/values.yaml` (under the OTLP exporter configuration) matches the token expected by your MLflow server. This token is required for the application to send traces to MLflow.

**Test connectivity:**
```bash
oc run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://mlflow.observability-hub.svc.cluster.local:5000/health
```

## Uninstallation

### Automated Uninstall

```bash
cd deploy/helm/observability
chmod +x uninstall.sh
./uninstall.sh
```

### Manual Uninstall

Uninstall in reverse order (resources first, then operators):

```bash
# Resources
helm uninstall mlflow -n observability-hub
helm uninstall logging-stack -n openshift-logging
helm uninstall grafana -n observability-hub
helm uninstall uwm
helm uninstall otel-collector -n observability-hub

# Operators (will also delete their namespaces)
helm uninstall otel-op
helm uninstall grafana-op
helm uninstall cluster-obs
helm uninstall logging-op
```

**Note:** Namespaces may take several minutes to fully terminate.

## Best Practices

- **Security:** Change default Grafana credentials in production
- **Storage:** Use production-grade object storage like OpenShift Data Foundation (ODF)
- **Retention:** Adjust LokiStack retention policies to manage costs
- **Performance:** Use log filtering to reduce unnecessary forwarding
- **Monitoring:** Set up alerts for critical AI workload metrics

## Additional Resources

- [OpenShift Logging Documentation](https://docs.openshift.com/container-platform/latest/observability/logging/cluster-logging.html)
- [Grafana Operator GitHub](https://github.com/grafana/grafana-operator)
- [OpenShift AI MLflow Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/working_with_mlflow/about-mlflow_mlflow)
- [vLLM Monitoring Guide](https://docs.vllm.ai/en/latest/serving/metrics.html)
