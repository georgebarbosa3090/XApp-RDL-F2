# ==============================================================================
# Script: deploy_dual_rdl_6xapps.ps1
# Finalidade: Implanta o ecossistema O-RAN completo de coexistência em PowerShell:
#             - Near-RT RIC (ricplt: DBAAS Redis, E2Term, SubMgr)
#             - H-RDL Fase 1 (ricxapp-iqos-xapp-rdl-f1: v1.1.0)
#             - CA-RDL Fase 2 (ricxapp-iqos-xapp-rdl-f2: v2.0.0)
#             - 6 Reference xApps (xSlice, Energy, TrafficSteering, Beamformer, ISAC, Rogue)
#             - Injetor Contínuo de Tráfego Service Mesh
# ==============================================================================

$ErrorActionPreference = "Stop"

$NAMESPACE_RIC = "ricplt"
$NAMESPACE_XAPP = "ricxapp"
$CLUSTER_NAME = "rancher-lab"
$CHART_DIR = "deploy/helm/iqos-xapp-rdl"

Write-Host "======================================================================" -ForegroundColor Blue
Write-Host "   Deploy Coexistencia O-RAN: H-RDL (F1) + CA-RDL (F2) + 6 xApps      " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Blue

# 1. Garantir Namespaces com Injeção Istio
Write-Host "`n[1/6] Configurando namespaces ricplt e ricxapp com injeção Istio..." -ForegroundColor Yellow
kubectl create namespace "$NAMESPACE_RIC" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "$NAMESPACE_XAPP" --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace "$NAMESPACE_RIC" istio-injection=enabled --overwrite 2>$null
kubectl label namespace "$NAMESPACE_XAPP" istio-injection=enabled --overwrite 2>$null

# 2. Sincronizar Imagens Docker nos Nós k3d
Write-Host "`n[2/6] Sincronizando imagens Docker (1.1.0 e 2.0.0)..." -ForegroundColor Yellow
if (Get-Command k3d -ErrorAction SilentlyContinue) {
    k3d image import iqos-xapp-rdl:1.1.0 -c $CLUSTER_NAME 2>$null
    k3d image import iqos-xapp-rdl:2.0.0 -c $CLUSTER_NAME 2>$null
}

# 3. Implantar Near-RT RIC (ricplt)
Write-Host "`n[3/6] Implantando Near-RT RIC (DBAAS Redis, E2Term, SubMgr)..." -ForegroundColor Yellow
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml -n "$NAMESPACE_RIC"
kubectl rollout status deployment/deployment-ricplt-dbaas-redis -n "$NAMESPACE_RIC" --timeout=60s

# 4. Implantar as 6 Reference xApps
Write-Host "`n[4/6] Implantando as 6 Reference xApps..." -ForegroundColor Yellow
kubectl apply -f deploy/kubernetes/reference-xapps-6set.yaml -n "$NAMESPACE_XAPP"

# 5. Implantar H-RDL Fase 1 e CA-RDL Fase 2 Concorrentes via Helm
Write-Host "`n[5/6] Implantando H-RDL (Fase 1) e CA-RDL (Fase 2) concorrentes..." -ForegroundColor Yellow

# 5.1 Release Fase 1 (H-RDL Determinística)
helm upgrade --install ricxapp-iqos-xapp-rdl-f1 $CHART_DIR `
  --namespace $NAMESPACE_XAPP `
  --set image.repository="iqos-xapp-rdl" `
  --set image.tag="1.1.0" `
  --set image.pullPolicy=Never `
  --set fullnameOverride="ricxapp-iqos-xapp-rdl-f1" `
  --set env.useFakeSdl="false" `
  --set env.rmrWaitForReady="false" `
  --set env.enableTorch="false"

# 5.2 Release Fase 2 (CA-RDL / MARL MAPPO)
helm upgrade --install ricxapp-iqos-xapp-rdl-f2 $CHART_DIR `
  --namespace $NAMESPACE_XAPP `
  --set image.repository="iqos-xapp-rdl" `
  --set image.tag="2.0.0" `
  --set image.pullPolicy=Never `
  --set fullnameOverride="ricxapp-iqos-xapp-rdl-f2" `
  --set env.useFakeSdl="false" `
  --set env.rmrWaitForReady="false" `
  --set env.enableTorch="true"

# 6. Validar Rollout e Subir Gerador de Carga
Write-Host "`n[6/6] Validando prontidão de todos os Pods e ativando injeção de tráfego..." -ForegroundColor Yellow
kubectl rollout status deployment/ricxapp-iqos-xapp-rdl-f1 -n $NAMESPACE_XAPP --timeout=60s
kubectl rollout status deployment/ricxapp-iqos-xapp-rdl-f2 -n $NAMESPACE_XAPP --timeout=60s
kubectl apply -f deploy/kubernetes/traffic-generator.yaml -n $NAMESPACE_XAPP

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "   Deploy Completo de Coexistência Concluído com SUCESSO!            " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "`n--- Pods Near-RT RIC (ricplt) ---"
kubectl get pods -n $NAMESPACE_RIC -o wide
Write-Host "`n--- Workloads Ativos no Mesh (ricxapp) ---"
kubectl get pods -n $NAMESPACE_XAPP -o wide
