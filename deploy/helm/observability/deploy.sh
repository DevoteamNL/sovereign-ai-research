#!/bin/bash

echo "🚀 Deploying Observability Resources..."
echo ""
echo "⚠️  Note: Run ./install-operators.sh first if you haven't already"
echo ""

echo "📦 Step 1: Installing OTEL Collector..."
helm upgrade --install otel-collector helm/otel-collector/ -n observability-hub
echo ""

echo "📦 Step 2: Installing User Workload Monitoring..."
helm upgrade --install uwm helm/uwm/
echo ""

echo "📦 Step 3: Installing Grafana..."
helm upgrade --install grafana helm/grafana/ -n observability-hub
echo ""

echo "📦 Step 4: Installing Logging Stack..."
helm upgrade --install logging-stack helm/logging-stack/ -n openshift-logging
echo ""

echo "📦 Step 5: Installing MLflow..."
helm upgrade --install mlflow helm/mlflow/ -n observability-hub
echo ""

echo "🎉 Observability resources deployed successfully!"
echo ""
echo "📊 Check status with:"
echo "  oc get pods -n observability-hub"
echo "  oc get grafana -n observability-hub"
echo "  oc get lokistack -n openshift-logging"
echo "  oc get pods -n openshift-logging"
echo "  oc get opentelemetrycollector -n observability-hub"
