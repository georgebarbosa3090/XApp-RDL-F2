# Energy Saving Reference xApp (Green RAN & Sleep Mode Optimizer)

## 1. Identificação e Propósito
* **Nome da xApp:** `energy_saving_orange`
* **Domínio de Atuação:** Eficiência Energética de Acesso de Rádio (Green RAN), Controle de Potência de Transmissão e Modo de Repouso (*Micro-Sleep*).
* **Prioridade de Controle:** `65` (Média-Baixa).
* **Referência de Origem:** [`Orange-OpenSource/ns-O-RAN-flexric`](https://github.com/Orange-OpenSource/ns-O-RAN-flexric) (`xapp_es_with_cell_util`).

---

## 2. Papel no Ecossistema xApp-RDL (Fase 1, 2 e 3)
* **Objetivo de Rádio:** Reduzir a pegada de carbono e o consumo elétrico dos transmissores da gNodeB em períodos de baixa ou média demanda, reduzindo a potência de transmissão para $15-20\text{ dBm}$ e desligando portadoras secundárias.
* **Dinâmica de Conflito (Cenário EEVS):**
  - **Conflito com xSlice / QoS:** Ao reduzir a potência $P_{tx}$, degrada o SINR na borda da célula e eleva a latência dos pacotes URLLC para $> 11\text{ ms}$, violando o SLA contratual de $5\text{ ms}$;
  - **Resolução RDL:** O motor RDL arbitra pela função de utilidade multiobjetivo EEVS (com penalidade sigmoide), ajustando a potência ótima em $19\text{ dBm}$, o que garante $+18.2\%$ de economia de energia com $0.0\%$ de quebra de SLA.

---

## 3. Interfaces O-RAN e Formato de Mensagens

### 3.1. Proposta de Ação RMR (`RDL_ACTION_PROPOSAL` - MsgType 30000)
```json
{
  "xapp_id": "energy_saving_orange",
  "node_id": "gnb_01",
  "parameter": "TX_POWER",
  "value": 20.0,
  "priority": 65,
  "slice_type": "BestEffort",
  "energy_target_kwh": 0.35,
  "timestamp": 1788445000.0
}
```

### 3.2. Mapeamento de Service Models E2
* **E2SM-RC (RAN Control):** Control Style 1 (Radio Resource Allocation), Action 1 (Modify Tx Power / Cell State).
* **E2SM-KPM (Key Performance Metrics):** Report Style 1 (`RRU.PrbTotDl`, `Energy.PowerConsumption`).

---

## 4. Endpoints HTTP e Métricas Prometheus

* **Portas Padrão:** HTTP `:8084` | Métricas `:8085` | RMR `:4562`
* **Endpoints:**
  * **Liveness Probe:** `GET http://localhost:8084/health` $\to$ `{"status": "UP", "xapp": "energy_saving_orange"}`
  * **Readiness Probe:** `GET http://localhost:8084/ready` $\to$ `{"ready": true}`
  * **Última Proposta:** `GET http://localhost:8084/proposals/latest`
  * **Métricas Prometheus:** `GET http://localhost:8084/metrics`
    - `es_proposals_total{node_id="gnb_01"}`: Contador de propostas de corte de energia emitidas;
    - `es_tx_power_target_dbm{node_id="gnb_01"}`: Potência alvo solicitada em dBm;
    - `es_estimated_energy_saved_ratio{node_id="gnb_01"}`: Fração estimada de economia energética.
