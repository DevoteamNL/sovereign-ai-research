#!/bin/bash

echo "🚀 Installing Observability Operators..."
echo ""

echo "📦 Step 1: Creating namespaces..."
oc create namespace observability-hub --dry-run=client -o yaml | oc apply -f -
oc create namespace openshift-user-workload-monitoring --dry-run=client -o yaml | oc apply -f -
echo "✅ Namespaces created"
echo ""

echo "📦 Step 2: Installing operators..."
helm upgrade --install cluster-obs helm/cluster-observability-operator/
helm upgrade --install grafana-op helm/grafana-operator/
helm upgrade --install otel-op helm/otel-operator/
helm upgrade --install logging-op helm/logging-operator/
echo "✅ Operators installed"
echo ""

echo "⏳ Waiting for operator CRDs to be ready (2-3 minutes)..."
echo ""

echo -n "   Waiting for OpenTelemetryCollector CRD..."
until oc get crd opentelemetrycollectors.opentelemetry.io >/dev/null 2>&1; do
  echo -n "."
  sleep 5
done
echo " ✓"

echo -n "   Waiting for Grafana CRD..."
until oc get crd grafanas.grafana.integreatly.org >/dev/null 2>&1; do
  echo -n "."
  sleep 5
done
echo " ✓"

echo -n "   Waiting for UIPlugin CRD..."
until oc get crd uiplugins.observability.openshift.io >/dev/null 2>&1; do
  echo -n "."
  sleep 5
done
echo " ✓"

echo -n "   Waiting for LokiStack CRD..."
until oc get crd lokistacks.loki.grafana.com >/dev/null 2>&1; do
  echo -n "."
  sleep 5
done
echo " ✓"

echo -n "   Waiting for ClusterLogForwarder CRD..."
until oc get crd clusterlogforwarders.observability.openshift.io >/dev/null 2>&1; do
  echo -n "."
  sleep 5
done
echo " ✓"

echo ""
echo "✅ All operators ready!"
echo ""
echo "📋 Next step: Run ./deploy.sh to deploy the observability resources"