# Beamformer Reference xApp (5G-Advanced Massive MIMO & Downtilt Optimizer)

## 1. Identificação e Propósito
* **Nome da xApp:** `beamformer_mimo_5ga`
* **Domínio de Atuação:** 5G-Advanced Massive MIMO (UPAs $16 \times 4$), Conformação de Feixes e Otimização de Tilt Elétrico Vertical (*Vertical Downtilt*).
* **Prioridade de Controle:** `75` (Intermediária-Alta).
* **Fatia Principal:** `eMBB` / `eMBB-Plus`.

---

## 2. Papel no Ecossistema xApp-RDL (Fase 2 / Fase 3)
* **Objetivo de Rádio:** Maximizar o SINR médio ($\bar{\gamma}_{DL}$) e a eficiência espectral ($\eta$), ajustando dinamicamente o ângulo de *downtilt* vertical entre $6^\circ$ e $8^\circ$ e os pesos de feixe da antena plana uniforme UPA $16 \times 4$ (64 elementos irradiantes) nas gNodeBs.
* **Dinâmica de Conflito:**
  - **Conflito com Traffic Steering:** O estreitamento ou inclinação de feixes altera subitamente a área de cobertura e o limiar $A_3\text{-Offset}$, forçando handovers desnecessários;
  - **Conflito com Slicing:** A alocação de feixes para usuários eMBB de alta vazão pode roubar potência de canais de controle de fatias URLLC;
  - **Resolução RDL:** O motor MAPPO (CTDE) avalia a interferência intercelular global no Crítico Centralizado e ajusta o *downtilt* de forma coordenada, suprimindo a interferência co-canal em $-18.8\text{ dBm}$.

---

## 3. Interfaces O-RAN e Formato de Mensagens

### 3.1. Proposta de Ação RMR (`RDL_ACTION_PROPOSAL` - MsgType 30000)
```json
{
  "xapp_id": "beamformer_mimo_5ga",
  "node_id": "gnb_01",
  "parameter": "VERTICAL_DOWNTILT",
  "value": 6.0,
  "priority": 75,
  "slice_type": "eMBB",
  "timestamp": 1788445000.0
}
```

### 3.2. Mapeamento de Service Models E2
* **E2SM-RC (RAN Control):** Control Style 10 (MIMO & Beam Management), Action 2 (Set Vertical Downtilt / Beam Weights).
* **E2SM-KPM (Key Performance Metrics):** Report Style 1 (`RRU.PrbTotDl`, `DRB.UEThpDl`, `SINR.P05`).

---

## 4. Endpoints HTTP e Métricas Prometheus

* **Portas Padrão:** HTTP `:8088` | Métricas `:8089` | RMR `:4565`
* **Endpoints:**
  * **Liveness Probe:** `GET http://localhost:8088/health` $\to$ `{"status": "UP", "xapp": "beamformer_mimo_5ga"}`
  * **Readiness Probe:** `GET http://localhost:8088/ready` $\to$ `{"ready": true}`
  * **Última Proposta:** `GET http://localhost:8088/proposals/latest`
  * **Métricas Prometheus:** `GET http://localhost:8088/metrics`
    - `beamformer_proposals_total{node_id="gnb_01", parameter="VERTICAL_DOWNTILT"}`: Contador de propostas de feixe emitidas;
    - `beamformer_downtilt_degrees{node_id="gnb_01"}`: Valor do tilt elétrico vertical solicitado ($^\circ$).
