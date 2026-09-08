# Volume 03: Guia de Implantação e Automação de Deploy (Helm & K8s Nativo)

**Documento:** Volume Temático 03  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Procedimentos de Implantação do Zero (Greenfield) e Deploy Isolado (Brownfield) no Cluster Kubernetes  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  
**Versão da Release:** `ricxapp-iqos-xapp-rdl-f2` | **Imagem:** `iqos-xapp-rdl:2.0.0`  

---

## 1. Visão Geral e Matriz de Cenários de Deploy

O ciclo de vida da **xApp RDL Fase 2 (CA-RDL / MARL)** suporta dois modos de implantação no cluster Kubernetes (k3d / K8s puro):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MATRIZ DE DEPLOY DA FASE 2                                │
├───────────────────────────────────┬────────────────────────────────────────────────────┤
│ Cenário A: Greenfield (Do Zero)   │ Cluster novo ou limpo:                             │
│                                   │ 1. Cria cluster k3d com portas O-RAN expostas      │
│                                   │ 2. Cria namespaces 'ricplt' e 'ricxapp'            │
│                                   │ 3. Instala Near-RT RIC (DBAAS Redis, RMR)          │
│                                   │ 4. Instala Reference xApps (QoS, Energy, TS, ...)  │
│                                   │ 5. Instala xApp RDL Fase 2 (CA-RDL / MARL)         │
├───────────────────────────────────┼────────────────────────────────────────────────────┤
│ Cenário B: Brownfield (Isolado)   │ Infraestrutura já ativa:                           │
│                                   │ 1. Mantém Near-RT RIC e Reference xApps operando   │
│                                   │ 2. Instala/Atualiza apenas a release               │
│                                   │    'ricxapp-iqos-xapp-rdl-f2' (v2.0.0)             │
└───────────────────────────────────┴────────────────────────────────────────────────────┘
```

---

## 2. Cenário A: Implantação Completa do Zero (Greenfield — Sem RIC, Sem xApps, Sem RDL)

Este cenário é o recomendado quando você está iniciando em uma máquina nova ou após recriar o ambiente. **Nenhum componente O-RAN precisa estar previamente instalado.**

### 2.1. Passo 1: Criar o Cluster Kubernetes (k3d) com Portas O-RAN Expostas
```bash
# Cria o cluster k3d com as portas O-RAN (SCTP 36422, HTTP 8080/8081, RMR 4560/4561):
make cluster-create

# Ou comando equivalente direto:
k3d cluster create rancher-lab \
  --servers 1 --agents 0 \
  --port "36422:36422/SCTP@server:0" \
  --port "8080:8080@server:0" \
  --port "8081:8081@server:0" \
  --port "4560:4560@server:0" \
  --port "4561:4561@server:0"
mkdir -p ~/.kube && k3d kubeconfig get rancher-lab > ~/.kube/config
```

### 2.2. Passo 2: Criar os Namespaces O-RAN
```bash
kubectl create namespace ricplt --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ricxapp --dry-run=client -o yaml | kubectl apply -f -
```

### 2.3. Passo 3: Implantar a Plataforma Near-RT RIC (`ricplt`)
Implanta o DBAAS Redis (Shared Data Layer - SDL) e serviços da plataforma:
```bash
# Aplica o manifesto do Near-RT RIC:
kubectl apply -f deploy/kubernetes/near-rt-ric.yaml -n ricplt

# Aguarda a prontidão do Redis DBAAS:
kubectl rollout status deployment/deployment-ricplt-dbaas-redis -n ricplt --timeout=90s
```

### 2.4. Passo 4: Implantar as Reference xApps (`ricxapp`)
Implanta as Reference xApps que fornecerão métricas e atuarão nas decisões de rede:
```bash
# Opção A: Script automatizado das 6 Reference xApps
bash scripts/deploy_reference_xapps.sh

# Opção B: Via Kustomize / Kubectl direto:
kubectl apply -f deploy/kubernetes/xapp-qos-xslice.yaml -n ricxapp
kubectl apply -f deploy/kubernetes/xapp-energy-saving.yaml -n ricxapp
kubectl apply -f deploy/kubernetes/xapp-traffic-steering.yaml -n ricxapp

# Valida o status dos pods das xApps:
kubectl get pods -n ricxapp -o wide
```

### 2.5. Passo 5: Compilar e Implantar a xApp RDL Fase 2 (CA-RDL / MARL)
```bash
# 1. Build da imagem Docker da Fase 2 (v2.0.0 com PyTorch / MARL):
make build

# 2. Deploy Helm da release dedicada:
make helm-deploy-f2
```

### 2.6. Pipeline Automatizado de Deploy Completo (Tudo em 1 Comando)
Você também pode executar a suíte completa de ponta a ponta:
```bash
# Executa a criação dos namespaces, deploy do RIC, deploy das 3 xApps e deploy da RDL:
bash scripts/deploy_k8s.sh --with-rdl
```

---

## 3. Cenário B: Implantação Incremental / Isolada (Brownfield — RIC e xApps já Ativos)

Utilize este cenário quando o Near-RT RIC e as Reference xApps já estiverem rodando no cluster e você deseja implantar ou atualizar **apenas** a xApp RDL Fase 2:

### 3.1. Implantar/Atualizar Exclusivamente a Release da Fase 2:
```bash
make helm-deploy-f2
```
*Premissa:* Não reinstala nem interrompe os componentes do `ricplt` nem as Reference xApps existentes.

### 3.2. Atualização Declarativa (Helm Upgrade):
```bash
make helm-upgrade-f2
```

---

## 4. Validação, Healthcheck e Monitoramento

### 4.1. Visualizar Status dos Pods em Todos os Namespaces:
```bash
# Namespace da Plataforma RIC:
kubectl get pods -n ricplt -o wide

# Namespace das xApps e RDL Fase 2:
kubectl get pods -n ricxapp -o wide
# ou: make status-f2
```

### 4.2. Inspecionar Logs da xApp RDL Fase 2 em Tempo Real:
```bash
make logs-f2
# ou: kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -f
```

### 4.3. Testar Endpoints HTTP e Telemetria Prometheus:
```bash
# Teste automatizado dos endpoints da Fase 2:
make test-f2

# Teste manual de Liveness / Readiness:
curl -i http://localhost:8080/health

# Métricas cognitivas do motor MAPPO / MARL:
curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_"

# Teste de integridade das Reference xApps:
make test-3xapps
```

---

## 5. Limpeza e Reset do Ambiente (Tear Down)

### 5.1. Desinstalar Apenas a xApp RDL Fase 2:
```bash
make helm-uninstall-f2
```

### 5.2. Desinstalar Todas as xApps (RDL Fase 1 e Fase 2):
```bash
make uninstall-all-rdl
```

### 5.3. Limpeza Completa (Destruir Cluster e Recursos):
```bash
# Remove o cluster k3d e todos os contêineres/volumes associados:
make cluster-delete
```

---

## 6. Mapeamento de Portas e Serviços O-RAN

| Serviço / Componente | Namespace | Tipo | Porta do Contêiner | Porta Mapeada no Host | Finalidade |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **xApp RDL F2 (HTTP)** | `ricxapp` | ClusterIP / NodePort | `8080` | `8080` | Sondas de Liveness/Readiness e API REST |
| **xApp RDL F2 (Metrics)** | `ricxapp` | ClusterIP / NodePort | `8081` | `8081` | Telemetria Prometheus e Métricas MARL |
| **xApp RDL F2 (RMR)** | `ricxapp` | ClusterIP | `4560` | `4560` | Barramento de Mensagens RMR O-RAN |
| **DBAAS (Redis SDL)** | `ricplt` | ClusterIP | `6379` | `6379` | Shared Data Layer (Estado e Contexto) |
| **E2Term / Mock** | `ricplt` | ClusterIP | `36422` | `36422/SCTP` | Terminação E2 / Conexão com simulador ns-3 |
| **QoS xSlice xApp** | `ricxapp` | ClusterIP | `8082` / `4562` | `8082` | Fatiamento de Rede e Controle de Banda |
| **Energy Saving xApp** | `ricxapp` | ClusterIP | `8084` / `4563` | `8084` | Desligamento de Células / Economia de Energia |
| **Traffic Steering xApp** | `ricxapp` | ClusterIP | `8086` / `4564` | `8086` | Handover e Redirecionamento de Tráfego |

---

## 7. Resumo dos Targets do Makefile

| Comando Makefile | Ação Executada | Escopo de Impacto |
| :--- | :--- | :--- |
| **`make cluster-create`** | Provisiona cluster k3d com portas O-RAN | Infraestrutura K8s |
| **`make cluster-delete`** | Destrói cluster k3d e limpa recursos | Infraestrutura K8s |
| **`make build`** | Compila a imagem Docker `iqos-xapp-rdl:2.0.0` | Imagem Local |
| **`make test`** | Executa os testes unitários (pytest) | Local |
| **`make helm-deploy-f2`** | Deploy exclusivo da release `ricxapp-iqos-xapp-rdl-f2` | Namespace `ricxapp` |
| **`make helm-upgrade-f2`** | Upgrade da release `ricxapp-iqos-xapp-rdl-f2` | Namespace `ricxapp` |
| **`make helm-uninstall-f2`** | Remove a release `ricxapp-iqos-xapp-rdl-f2` | Namespace `ricxapp` |
| **`make status-f2`** | Exibe status detalhado dos pods no namespace `ricxapp` | Diagnóstico |
| **`make logs-f2`** | Streaming de logs da xApp RDL Fase 2 | Diagnóstico |
| **`make test-f2`** | Testa endpoints `/health` e `/metrics` da Fase 2 | Diagnóstico |
| **`make test-3xapps`** | Verifica saúde das 3 Reference xApps | Diagnóstico |
