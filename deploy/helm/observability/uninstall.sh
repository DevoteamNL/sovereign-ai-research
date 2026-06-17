#!/bin/bash

echo "🗑️  Uninstalling Observability Stack..."
echo ""

echo "📦 Step 1: Uninstalling MLflow..."
helm uninstall mlflow -n observability-hub 2>/dev/null || echo "   (not installed)"
echo ""

echo "📦 Step 2: Uninstalling Logging Stack..."
helm uninstall logging-stack -n openshift-logging 2>/dev/null || echo "   (not installed)"
echo ""

echo "📦 Step 3: Uninstalling Grafana..."
helm uninstall grafana -n observability-hub 2>/dev/null || echo "   (not installed)"
echo ""

echo "📦 Step 4: Uninstalling User Workload Monitoring..."
helm uninstall uwm 2>/dev/null || echo "   (not installed)"
echo ""

echo "📦 Step 5: Uninstalling OTEL Collector..."
helm uninstall otel-collector -n observability-hub 2>/dev/null || echo "   (not installed)"
echo ""

echo "📦 Step 6: Uninstalling Operators (will also delete their namespaces)..."
helm uninstall otel-op 2>/dev/null || echo "   otel-op (not installed)"
helm uninstall grafana-op 2>/dev/null || echo "   grafana-op (not installed)"
helm uninstall cluster-obs 2>/dev/null || echo "   cluster-obs (not installed)"
helm uninstall logging-op 2>/dev/null || echo "   logging-op (not installed)"
echo ""

echo "✅ Observability stack uninstallation complete!"
echo ""
echo "Note: Namespaces and resources may take time to fully delete."
echo "Check with: oc get namespaces | grep -E 'observability|logging'"
