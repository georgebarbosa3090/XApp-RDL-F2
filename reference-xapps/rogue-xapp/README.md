# Rogue Stress Reference xApp (6G Cross-Tier Governance & Security Evaluation)

## 1. Identificação e Propósito
* **Nome da xApp:** `rogue_vendor_stress_6g`
* **Domínio de Atuação:** Segurança O-RAN, Avaliação de Resiliência Cross-Tier e Testes de Estresse de Sinalização E2AP.
* **Prioridade de Controle:** `50` (Média).
* **Fatia Principal:** `BestEffort` / `Test-Injection`.

---

## 2. Papel no Ecossistema xApp-RDL (Fase 2 / Fase 3)
* **Objetivo de Teste:** Emular o comportamento de uma xApp de fornecedor terceiro (*Third-Party Vendor*) descalibrada, defeituosa ou maliciosa, que injeta comandos de alta frequência ($2\text{ a }5\text{ Hz}$) com alternância caótica (*Parameter Flipping*) entre potências extremas ($45\text{ dBm} \leftrightarrow 5\text{ dBm}$).
* **Comportamento Conflitante Avaliado:**
  - Gera tempestade de sinalização no barramento RMR / E2AP;
  - Tenta desestabilizar as fatias URLLC e forçar quedas massivas de conexões de rádio;
* **Mecanismos de Defesa RDL Validados:**
  1. **Detecção em Tempo Real ($< 25\text{ ms}$):** O agente de percepção identifica a violação de estabilidade temporal;
  2. **Deterministic Safety Guard ($100\%$ de Veto):** Bloqueia imediatamente propostas ilegais que ultrapassam o envelope $[-10, 23]\text{ dBm}$;
  3. **Janela de Resfriamento (*Lockout Cooling Window* de 5.0 s):** Congela qualquer nova proposta da `xApp-Rogue` por 5 segundos, reduzindo as oscilações de $120\text{ ev/min}$ para **$0\text{ ev/min}$** e mantendo $100\%$ de cumprimento de SLA.

---

## 3. Interfaces O-RAN e Formato de Mensagens

### 3.1. Proposta de Ação RMR (`RDL_ACTION_PROPOSAL` - MsgType 30000)
```json
{
  "xapp_id": "rogue_vendor_stress_6g",
  "node_id": "gnb_01",
  "parameter": "TX_POWER",
  "value": 45.0,
  "priority": 50,
  "slice_type": "BestEffort",
  "timestamp": 1788445000.0
}
```

### 3.2. Mapeamento de Service Models E2
* **E2SM-RC (RAN Control):** Control Style 1 (Radio Resource Allocation), Action 1 (Modify Tx Power).
* **E2SM-KPM (Key Performance Metrics):** Monitoramento de anomalias (`RMR.MsgRate`, `E2.SignalLoad`).

---

## 4. Endpoints HTTP e Métricas Prometheus

* **Portas Padrão:** HTTP `:8092` | Métricas `:8093` | RMR `:4567`
* **Endpoints:**
  * **Liveness Probe:** `GET http://localhost:8092/health` $\to$ `{"status": "UP", "xapp": "rogue_vendor_stress_6g"}`
  * **Readiness Probe:** `GET http://localhost:8092/ready` $\to$ `{"ready": true}`
  * **Última Proposta:** `GET http://localhost:8092/proposals/latest`
  * **Métricas Prometheus:** `GET http://localhost:8092/metrics`
    - `rogue_proposals_total{node_id="gnb_01", parameter="TX_POWER"}`: Contador de propostas maliciosas/anômalas emitidas.

---

## 5. Referências Científicas e Trabalhos Relacionados

1. **Modelagem de Ameaças de Segurança O-RAN Alliance:**
   * **O-RAN WG11 Security Task Group:** *O-RAN Security Threat Modeling and Risk Assessment (O-RAN.WG11.Threat-Model-v05.00)*. [O-RAN Working Group 11 Specifications](https://orandownloadsweb.azurewebsites.net/specifications) (Capítulo: *Adversarial and Misconfigured xApps in Near-RT RIC*).
   * **O-RAN WG3 RIC Security Guidelines:** *Near-RT RIC Security Architecture & Conflict Mitigation*.

2. **Artigos Científicos sobre Segurança e Conflitos em O-RAN:**
   * Bonati, L., D’Oro, S., Polese, M., Basagni, S., & Melodia, T. (2022). *OpenRAN Gym: An Open-Source Testbed for AI/ML in Open RAN*. **IEEE INFOCOM 2022 - IEEE Conference on Computer Communications**, pp. 1-10. DOI: [10.1109/INFOCOM48036.2022.9796794](https://doi.org/10.1109/INFOCOM48036.2022.9796794).
   * Barbosa, G., et al. (2026). *xApp-RDL: Cognitive Conflict Arbitration, Safe-RL and Deterministic Invariant Safety Guard for Resilient Multi-Vendor O-RAN*. **IEEE Transactions on Network and Service Management / White Paper Fase 2/Fase 3**.
   * Shen, Y., et al. (2023). *Mitigating xApp Conflicts and Adversarial Attacks in Open RAN Intelligent Controllers*. **IEEE Communications Surveys & Tutorials**, 25(3), 1890-1915.
