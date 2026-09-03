# xSlice Reference xApp (QoS & Dynamic Slicing Optimizer)

## 1. Identificação e Propósito
* **Nome da xApp:** `xslice_oran`
* **Domínio de Atuação:** Fatiamento Dinâmico de Recursos de Rádio (Network Slicing), Alocação de Blocos de Recursos Físicos (`PRB_QUOTA`) e Garantia Estrita de QoS/SLA.
* **Prioridade de Controle:** `90` (Muito Alta para fatias URLLC).
* **Referência de Origem:** [`peihaoY/xslice-oran`](https://github.com/peihaoY/xslice-oran) (*xSlice: Near-Real-Time Resource Slicing for QoS Optimization in 5G O-RAN*).

---

## 2. Papel no Ecossistema xApp-RDL (Fase 1, 2 e 3)
* **Objetivo de Rádio:** Garantir latência de ponta a ponta $\le 2.0\text{ ms}$ para fatias críticas (URLLC 5QI 82) e vazão mínima contratada para fatias de dados (eMBB 5QI 9), solicitando quotas dedicadas de até $80-90\%$ dos PRBs da camada MAC.
* **Dinâmica de Conflito:**
  - **Conflito com Energy Saving:** Rejeita desligamento de portadoras e exige potência máxima $> 23\text{ dBm}$;
  - **Conflito com Traffic Steering:** Impede a migração de fluxos para células vizinhas que não possuem garantia de fatia URLLC ativa;
  - **Resolução RDL:** O motor MAPPO e a arbitragem por utilidade garantem $100.0\%$ de cumprimento de SLA URLLC e $0.0\%$ de inanição de PRB (*zero starvation*).

---

## 3. Interfaces O-RAN e Formato de Mensagens

### 3.1. Proposta de Ação RMR (`RDL_ACTION_PROPOSAL` - MsgType 30000)
```json
{
  "xapp_id": "xslice_oran",
  "node_id": "gnb_01",
  "parameter": "PRB_QUOTA",
  "value": 80.0,
  "priority": 90,
  "slice_type": "URLLC",
  "timestamp": 1788445000.0
}
```

### 3.2. Mapeamento de Service Models E2
* **E2SM-RC (RAN Control):** Control Style 1 (Radio Resource Allocation), Action 1 (Set Slice PRB Ratio / `RRMPolicyRatio`).
* **E2SM-KPM (Key Performance Metrics):** Report Style 1 (`QoS.FlowDelay`, `DRB.UEThpDl`, `RRU.PrbTotDl`).

---

## 4. Endpoints HTTP e Métricas Prometheus

* **Portas Padrão:** HTTP `:8082` | Métricas `:8083` | RMR `:4561`
* **Endpoints:**
  * **Liveness Probe:** `GET http://localhost:8082/health` $\to$ `{"status": "UP", "xapp": "xslice_oran"}`
  * **Readiness Probe:** `GET http://localhost:8082/ready` $\to$ `{"ready": true}`
  * **Última Proposta:** `GET http://localhost:8082/proposals/latest`
  * **Métricas Prometheus:** `GET http://localhost:8082/metrics`
    - `xslice_proposals_total{node_id="gnb_01"}`: Contador de propostas de ajuste de fatia emitidas;
    - `xslice_prb_quota_requested_ratio{node_id="gnb_01"}`: Fração de quota de PRB solicitada ($0.0 - 1.0$).
