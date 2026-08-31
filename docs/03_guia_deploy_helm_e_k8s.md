# Volume 03: Guia de Implantação Helm Exclusivo para RDL Fase 2 (CA-RDL / MARL)

**Documento:** Volume Temático 03  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Procedimento de Deploy Helm Isolado da Release `ricxapp-iqos-xapp-rdl-f2` no Near-RT RIC Existente  
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
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        Cluster Kubernetes: Namespace ricxapp                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [ricxapp-qos-xslice]          (Existente - Já em Execução)                           │
│   [ricxapp-energy-saving]       (Existente - Já em Execução)                           │
│   [ricxapp-traffic-steering]    (Existente - Já em Execução)                           │
│                                                                                        │
│   ─────────────────────────── [Deploy Isolado Fase 2] ────────────────────────────     │
│   [ricxapp-iqos-xapp-rdl-f2]    (v2.0.0 - CA-RDL / MARL - Release Dedicada)           │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Comandos Operacionais de Deploy da Fase 2

### 2.1. Implantar Exclusivamente a xApp RDL Fase 2:
```bash
# Executa o build da imagem 2.0.0, importação no k3d e deploy da release 'ricxapp-iqos-xapp-rdl-f2'
make helm-deploy-f2
```
*Esse comando não reinstala o Near-RT RIC nem interfere nas 3 Reference xApps existentes.*

### 2.2. Verificar o Status da xApp RDL Fase 2:
```bash
make status-f2
# ou: kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -o wide
```

### 2.3. Inspecionar Logs do Motor MARL/MAPPO em Tempo Real:
```bash
make logs-f2
# ou: kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -f
```

### 2.4. Validar Endpoints HTTP e Telemetria Prometheus:
```bash
# Testa o healthcheck e métricas cognitivas da Fase 2
make test-f2

# Chamadas manuais via cURL:
curl -i http://localhost:8080/health
curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_"
```

### 2.5. Remover Apenas a xApp RDL Fase 2:
```bash
# Desinstala somente a release 'ricxapp-iqos-xapp-rdl-f2' mantendo o restante da infraestrutura intacta
make helm-uninstall-f2
```

---

## 3. Resumo dos Targets do Makefile para a Fase 2

| Comando Makefile | Ação Executada | Escopo de Impacto |
| :--- | :--- | :--- |
| **`make test`** | Executa os 18 testes unitários (pytest) | Local |
| **`make helm-deploy-f2`** | Instala/Atualiza a release `ricxapp-iqos-xapp-rdl-f2` (v2.0.0) | Namespace `ricxapp` (apenas RDL F2) |
| **`make helm-uninstall-f2`** | Desinstala a release `ricxapp-iqos-xapp-rdl-f2` | Namespace `ricxapp` (apenas RDL F2) |
| **`make status-f2`** | Exibe o status detalhado dos pods no namespace `ricxapp` | Somente leitura |
| **`make logs-f2`** | Abre streaming dos logs da xApp RDL Fase 2 | Somente leitura |
| **`make test-f2`** | Testa `/health` (`:8080`) e `/metrics` (`:8081`) da Fase 2 | Somente leitura |
| **`make run-suite`** | Executa simulações ns-3 e benchmark de Machine Learning | Suíte experimental |
