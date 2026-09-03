# ISAC Radar Reference xApp (6G Integrated Sensing and Communication)

## 1. Identificação e Propósito
* **Nome da xApp:** `isac_radar_sensing_6g`
* **Domínio de Atuação:** Redes 6G AI-Native (IMT-2030), Sensoriamento Ambiental Integrado à Comunicação (ISAC) em ondas milimétricas ($28\text{ GHz}, 400\text{ MHz}$).
* **Prioridade de Controle:** `85` (Alta).
* **Fatia Principal:** `SENSING` / `URLLC-Safety`.

---

## 2. Papel no Ecossistema xApp-RDL (Fase 2 / Fase 3)
* **Objetivo de Rádio:** Garantir resolução espacial de radar $\Delta R \le 0.5\text{ m}$ ($\Delta R = \frac{c}{2B}$) e probabilidade de detecção de alvos móveis $P_d \ge 95\%$ (drones aéreos e veículos autônomos), solicitando uma fração de recursos de símbolos OFDM (`SENSING_RATIO = 0.35`).
* **Dinâmica de Conflito:**
  - **Conflito com eMBB-Plus:** A reserva de subportadoras e símbolos OFDM para pulsos de eco radar reduz a vazão bruta de dados de usuários móveis e transmissões holográficas;
  - **Resolução RDL:** O motor Safe-RL (CMDP - Constrained MDP) da RDL estabelece um envelope restrito de probabilidade de radar enquanto aloca os símbolos restantes para maximizar o throughput de dados, garantindo $98.7\%$ de cumprimento de SLA ISAC e $> 1.4\text{ Gbps}$ agregado.

---

## 3. Interfaces O-RAN e Formato de Mensagens

### 3.1. Proposta de Ação RMR (`RDL_ACTION_PROPOSAL` - MsgType 30000)
```json
{
  "xapp_id": "isac_radar_sensing_6g",
  "node_id": "gnb_01",
  "parameter": "SENSING_RATIO",
  "value": 0.35,
  "priority": 85,
  "slice_type": "SENSING",
  "timestamp": 1788445000.0
}
```

### 3.2. Mapeamento de Service Models E2
* **E2SM-RC (RAN Control):** Control Style 12 (ISAC & Sensing Subcarrier Allocation), Action 1 (Set Sensing Symbol Ratio).
* **E2SM-KPM (Key Performance Metrics):** Report Style 1 (`SENSING.DetectionProb`, `SENSING.RangeResolution`, `DRB.UEThpDl`).

---

## 4. Endpoints HTTP e Métricas Prometheus

* **Portas Padrão:** HTTP `:8090` | Métricas `:8091` | RMR `:4566`
* **Endpoints:**
  * **Liveness Probe:** `GET http://localhost:8090/health` $\to$ `{"status": "UP", "xapp": "isac_radar_sensing_6g"}`
  * **Readiness Probe:** `GET http://localhost:8090/ready` $\to$ `{"ready": true}`
  * **Última Proposta:** `GET http://localhost:8090/proposals/latest`
  * **Métricas Prometheus:** `GET http://localhost:8090/metrics`
    - `isac_radar_proposals_total{node_id="gnb_01"}`: Total de propostas de alocação de sensoriamento emitidas;
    - `isac_radar_sensing_ratio{node_id="gnb_01"}`: Fração de recursos de rádio solicitados para sensoriamento ($0.0 - 1.0$).
