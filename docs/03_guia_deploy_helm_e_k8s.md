# Volume 03: Guia de Implantação Helm Exclusivo para RDL Fase 2 (CA-RDL / MARL)

**Documento:** Volume Temático 03  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Procedimento de Deploy Helm Isolado da Release `ricxapp-iqos-xapp-rdl-f2` no Near-RT RIC Existente com Monitoramento em Tempo Real  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  
**Versão da Release:** `ricxapp-iqos-xapp-rdl-f2` | **Imagem:** `iqos-xapp-rdl:2.0.0`  

---

## 1. Premissas de Implantação da Fase 2

Na infraestrutura operacional de testes e produção:
1. O **Near-RT RIC Platform (`ricplt`)** já está provisionado e ativo (DBAAS Redis na porta `6379`, E2Term na porta `36422/SCTP`, E2Mgr e Route Generator na porta `4561`).
2. As **3 Reference xApps (`ricxapp`)** já estão implantadas e em execução:
   - `ricxapp-qos-xslice` (porta HTTP `8082`, RMR `4562`)
   - `ricxapp-energy-saving` (porta HTTP `8084`, RMR `4563`)
   - `ricxapp-traffic-steering` (porta HTTP `8086`, RMR `4564`)
3. A **xApp RDL Fase 2 (CA-RDL)** deve ser implantada de forma **isolada e independente**, com identificação exclusiva de release:
   - **Helm Release Name:** `ricxapp-iqos-xapp-rdl-f2`
   - **Deployment Name:** `ricxapp-iqos-xapp-rdl-f2`
   - **Tag da Imagem:** `2.0.0`
   - **Target de Execução:** `make helm-deploy-f2`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Cluster Kubernetes: Namespace ricxapp                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   [ricxapp-qos-xslice]          (Existente - Já em Execução)                │
│   [ricxapp-energy-saving]       (Existente - Já em Execução)                │
│   [ricxapp-traffic-steering]    (Existente - Já em Execução)                │
│                                                                             │
│   ─────────────────────────── [Deploy Isolado Fase 2] ───────────────────── │
│   [ricxapp-iqos-xapp-rdl-f2]    (v2.0.0 - CA-RDL / MARL - Release Dedicada) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Comandos Operacionais de Deploy e Acompanhamento em Tempo Real

### 2.1. Implantar Exclusivamente a xApp RDL Fase 2:
```bash
# Executa o build da imagem 2.0.0, importação no k3d e deploy da release 'ricxapp-iqos-xapp-rdl-f2'
make helm-deploy-f2
# OU
bash scripts/deploy_rdl_phase2.sh
```

### 2.2. Monitorar o Ciclo de Vida dos Pods em Tempo Real (`-w`):
```bash
kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -w
```

### 2.3. Streaming de Logs do Motor MARL/MAPPO em Tempo Real (`-f`):
```bash
# Via Makefile:
make logs-f2

# Via Kubectl direto (PowerShell, CMD ou Bash):
kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -f
```

### 2.4. Validar Endpoints HTTP e Telemetria Prometheus:
```bash
# Testa o healthcheck e métricas cognitivas da Fase 2
make test-f2

# Chamadas manuais via cURL:
curl -i http://localhost:8080/health
curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_"
```

### 2.5. Comandos para Desinstalar a xApp RDL (Fase 1 e Fase 2):

#### 2.5.1. Desinstalar xApp RDL Fase 1 (H-RDL Heurística):
```bash
# Via Makefile:
make helm-uninstall-f1

# Via Helm direto:
helm uninstall ricxapp-iqos-xapp-rdl -n ricxapp
```

#### 2.5.2. Desinstalar xApp RDL Fase 2 (CA-RDL / MARL):
```bash
# Via Makefile:
make helm-uninstall-f2

# Via Helm direto:
helm uninstall ricxapp-iqos-xapp-rdl-f2 -n ricxapp
```

#### 2.5.3. Desinstalação Simultânea de Todas as Versões RDL:
```bash
# Desinstala ambas as releases mantendo as 3 reference xApps ativas:
make uninstall-all-rdl
```

---

## 3. Resumo dos Targets do Makefile para a Fase 2

| Comando Makefile | Ação Executada | Escopo de Impacto |
| :--- | :--- | :--- |
| **`make test`** | Executa os 18 testes unitários (pytest) | Local |
| **`make helm-deploy-f2`** | Instala/Atualiza a release `ricxapp-iqos-xapp-rdl-f2` (v2.0.0) | Namespace `ricxapp` (apenas RDL F2) |
| **`make helm-uninstall-f1`** | Desinstala a release `ricxapp-iqos-xapp-rdl` (Fase 1) | Namespace `ricxapp` (apenas RDL F1) |
| **`make helm-uninstall-f2`** | Desinstala a release `ricxapp-iqos-xapp-rdl-f2` (Fase 2) | Namespace `ricxapp` (apenas RDL F2) |
| **`make uninstall-all-rdl`** | Desinstala ambas as releases RDL (Fase 1 e Fase 2) | Namespace `ricxapp` (apenas RDLs) |
| **`make status-f2`** | Exibe o status detalhado dos pods no namespace `ricxapp` | Somente leitura |
| **`make logs-f2`** | Abre streaming dos logs da xApp RDL Fase 2 | Somente leitura |
| **`make test-f2`** | Testa `/health` (`:8080`) e `/metrics` (`:8081`) da Fase 2 | Somente leitura |
| **`make run-suite`** | Executa simulações ns-3 e benchmark de Machine Learning | Suíte experimental |

