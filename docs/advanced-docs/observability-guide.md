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
oc get consolelink | grep -i mlflow
```

**Use cases:**
- Track ML experiments and agent traces
- Log model parameters, metrics, and artifacts
- Compare experiment runs
- Register and version models

#### Configuring AI-Q Application to Send Traces to MLflow

After deploying the AI-Q application, you need to configure it to send traces to MLflow:

**Step 1: Extract the ServiceAccount token**

The AI-Q backend automatically creates a long-lived token when deployed. Extract it:

```bash
# Get the auto-generated token
oc get secret long-lived-api-token -n ns-aiq -o jsonpath='{.data.token}' | base64 -d
```

Copy this token value.

**Step 2: Update the AI-Q values file**

Edit `deploy/helm/aiq-rh/values.yaml` and replace `{YOUR_TOKEN_HERE}` with the token from Step 1:

```yaml
# Find this section in values.yaml (around line 80-90)
otlp:
  enabled: true
  exporter:
    endpoint: https://mlflow.observability-hub.svc.cluster.local:8443/v1/traces
    headers:
      x-mlflow-experiment-id: "1"
      x-mlflow-workspace: "ns-aiq"
      Authorization: "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."  # <-- Replace with your token
```

**Step 3: Upgrade the AI-Q deployment**

Apply the updated configuration:

```bash
cd deploy/helm
helm upgrade aiq aiq-rh/ -n ns-aiq \
  -f aiq-rh/values-vllm.yaml \
  -f aiq-rh/values-branding.yaml
```

**Step 4: Restart the backend pod**

Force the backend to reload with the new token:

```bash
oc rollout restart deployment/aiq-backend -n ns-aiq

# Wait for the pod to be ready
oc rollout status deployment/aiq-backend -n ns-aiq
```

**Step 5: Create an MLflow experiment**

Navigate to the MLflow UI (get URL from command above) and create an experiment to receive traces:

1. Open the MLflow UI in your browser
2. Click **"+ Create Experiment"** (or **"New Experiment"**)
3. Enter experiment details:
   - **Name:** `aiq-research-agent-traces`
   - **Artifact Location:** (leave default)
   - **Tags:** (optional) Add tags like `environment:dev`, `project:aiq`
4. Click **"Create"**
5. Note the **Experiment ID** (should be `1` if this is your first experiment)

**Verify the experiment ID matches your configuration:**

The experiment ID in MLflow should match the `x-mlflow-experiment-id` header in your `values.yaml`. If it doesn't match, either:
- Update `values.yaml` with the correct ID and re-run Step 3-4
- Or delete and recreate the experiment to get ID `1`

**Step 6: Test trace collection**

Generate some activity in the AI-Q application:

```bash
# Get the AI-Q frontend URL
echo "https://$(oc get route aiq-frontend -n ns-aiq -o jsonpath='{.spec.host}')"
```

Open the UI and run a research query. Then check MLflow for traces:

1. Go to MLflow UI
2. Click on the `aiq-research-agent-traces` experiment
3. You should see traces appearing under the "Runs" or "Traces" tab

If traces don't appear, check the [Troubleshooting](#mlflow-connection-issues) section below.

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

**Traces not appearing in MLflow?**

1. **Verify you completed all configuration steps** in the [Configuring AI-Q Application to Send Traces to MLflow](#configuring-ai-q-application-to-send-traces-to-mlflow) section above
2. **Check the experiment ID matches** between MLflow UI and `values.yaml` (`x-mlflow-experiment-id`)
3. **Verify the token is correct** - re-extract and compare with `values.yaml`
4. **Check backend pod logs for OTLP errors:**

```bash
oc logs -n ns-aiq deployment/aiq-backend | grep -i "otlp\|mlflow\|trace"
```

**Check MLflow deployment:**
```bash
oc get deployment mlflow -n redhat-ods-applications
oc logs -n redhat-ods-applications deployment/mlflow --tail=50
```

**Test connectivity from AI-Q namespace:**
```bash
oc run -it --rm debug --image=curlimages/curl --restart=Never -n ns-aiq -- \
  curl -k https://mlflow.observability-hub.svc.cluster.local:8443/health
```

**Common issues:**
- Token not updated after initial deployment
- Experiment ID mismatch between MLflow and values.yaml
- Backend pod not restarted after values update

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
helm uninstall mlflow -n redhat-ods-applications
helm uninstall logging-stack -n openshift-logging
helm uninstall grafana -n observability-hub
helm uninstall uwm
helm uninstall otel-collector -n observability-hub

# Clean up orphaned User Workload Monitoring ConfigMap
oc delete configmap user-workload-monitoring-config -n openshift-user-workload-monitoring 2>/dev/null || true

# Operators (will also delete their namespaces)
helm uninstall otel-op
helm uninstall grafana-op
helm uninstall cluster-obs
helm uninstall logging-op
```

**Note:** Namespaces may take several minutes to fully terminate. The User Workload Monitoring ConfigMap is managed by the cluster-monitoring-operator and may persist after Helm uninstall, which can cause conflicts on reinstall.

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
