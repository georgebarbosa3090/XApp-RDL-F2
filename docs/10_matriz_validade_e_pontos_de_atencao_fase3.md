# Volume 10: Matriz de Validade, Arquitetura Hierárquica e Pontos de Atenção Críticos — RDL Fase 3

## Governança Cognitiva Escalonada e Mitigação Híbrida de Conflitos em O-RAN (5G-Adv/6G)

---

## 1. Resumo Executivo da Evolução Arquitetural

A evolução da **xApp-RDL** da Fase 2 para a Fase 3 consolida uma mudança de paradigma essencial respaldada pela literatura mais recente de O-RAN (*6G-SMART MLO 2026, COMIX 2025, ORIGAMI PIOR 2026, Wadud et al. 2026 e Zolghadr et al. 2025*): **a mitigação de conflitos e a coordenação de recursos de rádio não devem ser tratadas como um problema monolítico de aprendizado por reforço**.

Em vez disso, a xApp-RDL opera sob um **Motor de Decisão Hierárquico Escalonado em 3 Níveis** com um **Safety Guard Invariante Determinístico**:

```
                       Propostas das xApps (ActionProposals)
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAMADA 1: HEURÍSTICA RÁPIDA (H-RDL)                      │
│                [Critério: C(c, s) ≤ τ₁  |  Latência < 1 ms]                 │
│                                                                             │
│  - Resolução Determinística para Conflitos Diretos com Prioridade Definida │
│  - Aplicação de Regras de Precedência (ORIGAMI PIOR: Φ(a_k))                │
│  - Checagem Estática de Limites Físicos de Hardware e Domínio de Parâmetro  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Se C(c,s) > τ₁ (Conflito Não Trivial)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 CAMADA 2: CONTEXT-AWARE & COGNITIVA (CA-RDL)                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Nível 2A: Utilidade Contextual & Digital Twin (τ₁ < C(c, s) ≤ τ₂)     │  │
│  │  - Avaliação Combinatória Proativa do Power Set 2^N (6G-SMART MLO)   │  │
│  │  - Políticas de Seleção Multi-Objetivo (COMIX: MaxTS, EES, TVS, EEVS) │  │
│  │  - Predição Forward-Rolling de 5s via Ensembles XGBoost              │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │ Se C(c,s) > τ₂ (Alta Complexidade)    │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │ Nível 2B: Coordenação Multiagente com MAPPO (C(c, s) > τ₂)            │  │
│  │  - Treinamento Centralizado com Execução Descentralizada (CTDE)      │  │
│  │  - Conflitos Indiretos e Implícitos Não-Lineares de Alta Dimensão     │  │
│  │  - Grafo de Conhecimento Semântico (Neo4j / GraphSAGE)                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  CAMADA 3: INVARIANTE - SAFETY GUARD & ARBITER              │
│  - Verificação Determinística Pós-Inferência (Limites de Potência e PRB)   │
│  - Validação de Políticas A1 do Operador (Non-RT RIC)                       │
│  - Janela de Resfriamento (Lockout de 5s Anti-Ping-Pong)                    │
│  - Emissão E2SM-RC Format 1 / Format 2 (RIC_CONTROL_REQUEST via RMR %meid)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Matriz de Validade Científica e Operacional

| Dimensão de Validade | Risco / Vulnerabilidade Observada | Mitigação Arquitetural e Metodológica (Fase 3) | Evidência de Suporte na Literatura |
| :--- | :--- | :--- | :--- |
| **1. Validade Interna (Algorítmica e Convergência)** | • Instabilidade de treinamento do PPO.<br/>• *Reward hacking* em formulações heurísticas.<br/>• Vazamento de informação global no Ator. | • Adoção de **CTDE estrito** com Crítico Global $V_\psi(s)$ e Atores locais $\pi_{\theta_i}(a_i \| o_i)$.<br/>• **Generalized Advantage Estimation (GAE)** com $\lambda = 0.95, \gamma = 0.99$.<br/>• Normalização de recompensas em $[0, 1]$ e regularização por entropia.<br/>• **Self-Distillation MAPPO (SD-MAPPO)**. | *Li et al. (MAPPO 2023)*<br/>*Zhang et al. (MAPPO-LCR 2026)*<br/>*Barbosa (RDL Cap. 5 2026)* |
| **2. Validade Temporal (Near-RT Loop Budget)** | • Latência de inferência neural ultrapassar o prazo de 10 ms – 1 s do Near-RT RIC.<br/>• Overhead de serialização ASN.1. | • **Escalonamento Híbrido:** Conflitos triviais resolvidos em $< 1\text{ ms}$ (H-RDL).<br/>• Conflitos complexos avaliados em $< 76\text{ ms}$ ($O(2^N \cdot M)$ com XGBoost/MAPPO).<br/>• Decodificação rápida APER nativa via `pycrate` e `xDevSM` ($< 100\ \mu\text{s}$). | *Kurtulan et al. (ITU J-FET 2026)*<br/>*Feraudo et al. (ACM xDevSM 2024)*<br/>*Santos et al. (IEEE 2025)* |
| **3. Estabilidade de Sinalização e Anti-Flapping** | • *Parameter Flipping* e oscilações cíclicas de controle (*ping-pong*) entre xApps concorrentes.<br/>• *Integrator wind-up* em loops desacoplados. | • **Janela de Resfriamento / Lockout de 5 s:** xApps com ações rejeitadas são bloqueadas por 5 s, alinhado com o horizonte de predição *forward-rolling* de 5 s do modelo preditivo. | *Kurtulan et al. (6G-SMART MLO 2026)*<br/>*Rahman et al. (ORIGAMI PIOR 2026)* |
| **4. Validade de Construção (Conformidade O-RAN)** | • Suposição de interfaces inexistentes ou não-padronizadas.<br/>• Incompatibilidade de Service Models entre fornecedores. | • Conformidade com especificações **O-RAN WG3 (E2AP v2.02/v3.0, E2SM-KPM v3.0, E2SM-RC v1.03)**.<br/>• Subscrição REST com o SubMgr e rotas RMR com tag `%meid`.<br/>• Mapeamento padronizado de parâmetros (Power Control Style 2, A3 Offset Style 3, PRB Quota Style 1). | *Santos et al. (Zero-to-Hero 2025)*<br/>*O-RAN.WG3.TS.E2SM-RC*<br/>*O-RAN.WG3.TS.E2SM-KPM* |
| **5. Validade Externa e Sim-to-Real** | • Políticas treinadas em modelos toy não transferem para o ambiente físico real. | • Treinamento no Digital Twin de alta fidelidade **NORI (NS-3.42 + 5G-LENA)** com modelo de propagação híbrido de 3 camadas (UMi 3.5 GHz, Sombreamento $7\text{ dB}$, Phased-Array UPA 16x4).<br/>• Validação em topologia urbana realista derivada do **OpenCellID (Dublin City Center)**. | *Oliveira et al. (SBrT 2025)*<br/>*Wadud et al. (Comput. Netw. 2026)*<br/>*Bonati et al. (OpenRAN Gym 2022)* |
| **6. Validade Estatística e Reprodutibilidade** | • Avaliação baseada em poucas sementes com variabilidade estocástica oculta.<br/>• Desbalanceamento severo de classes ($< 10\%$ de conflitos reais). | • Conjunto experimental com **$\ge 200$ sementes RNG independentes** com zero overlap em relação ao treino.<br/>• Avaliação de **Macro-F1 com SMOTE-GNN** para balanceamento da classe minoritária.<br/>• Testes estatísticos pareados bicaudais ($p < 0.001$) e intervalos de confiança de 95%. | *Wadud et al. (GenC & SMOTE-GNN 2026)*<br/>*Zolghadr et al. (GraphSAGE 2025)* |
| **7. Segurança Operacional Invariante** | • Ações geradas por exploração neural ou xApps maliciosas causarem colapso de cobertura ou quebra de SLA. | • **Safety Guard Independente e Determinístico:** Toda ação passa por verificação estrita de limites físicos (potência, PRB, intervalo) e intenções A1 antes da emissão ao E2 Node. | *Giannopoulos et al. (COMIX 2025)*<br/>*Barbosa (RDL Cap. 6 2026)* |

---

## 3. Soluções Concretas Implementadas no Código

### 3.1. MAPPO com GAE Completo e CTDE Real ([`src/agents/marl/mappo_agent.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/marl/mappo_agent.py))
- **Buffer de Rollout Operacional:** Coleta transições completas contendo $(o_t, s_t^{\text{global}}, a_t, \log \pi(a_t), r_t, d_t)$.
- **Cálculo Real de GAE:**
  $$\delta_t = r_t + \gamma V(s_{t+1}) (1 - d_t) - V(s_t), \quad \hat{A}_t = \delta_t + \gamma \lambda (1 - d_t) \hat{A}_{t+1}$$
- **Otimização por Gradiente Adam:** Atualização iterativa de pesos do Ator (clipped objective com termo de entropia) e do Crítico (MSE Loss) em múltiplas épocas PPO.
- **Coordenação Multiagente Efetiva:** A função `decide()` consulta a política de cada agente envolvido e combina o valor do Crítico Centralizado e a recompensa multi-objetivo normalizada.

### 3.2. Motor de Raciocínio Hierárquico Escalonado ([`src/agents/reasoning_agent.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/agents/reasoning_agent.py))
- **Estimador de Complexidade $C(c, s)$:** Roteia conflitos diretos simples para o Nível 1 ($< 1\text{ ms}$), conflitos multi-objetivo para o Nível 2A (Utilidade Contextual / NDT Proativo) e conflitos não-lineares de alta dimensão para o Nível 2B (MAPPO).
- **Janela de Resfriamento (Lockout de 5s):** Bloqueia reenvio de ações conflitantes rejeitadas durante 5 segundos para suprimir oscilações de controle.
- **Ingestão Dinâmica de Telemetria KPM:** O estado da rede é alimentado diretamente a partir do relatório KPM decodificado pela camada de percepção (`DRB.UEThpDl`, `QoS.FlowDelay`, `RRU.PrbTotDl`).

---

## 4. Pontos de Atenção Críticos para a Fase 3

1. **Compilação C++ Nativa / ONNX TensorRT:**
   Para alcançar latência sub-milissegundo ($< 1\text{ ms}$) em produção no Near-RT RIC, exportar os modelos PyTorch treinados para o formato ONNX e executar via runtime C++ com aceleração de hardware.
2. **Integração Real com o Módulo NORI no ns-3.42:**
   Utilizar a interface padronizada do `NoriE2Interface` e `e2sim_lib` (E2AP v2.02.03) para executar simulações closed-loop conectadas diretamente ao cluster Kubernetes do Near-RT RIC (k3d/Rancher).
3. **Padrão Zero-Trust e Isolamento de Rogue xApps:**
   Implementar métricas de anomalia comportamental no módulo de percepção para detectar xApps que violem sistematicamente as restrições ou gerem flooding de propostas conflitantes.
4. **Governança de Snapshots Locais:**
   Manter snapshots e backups diários através do script automatizado [`scripts/create_daily_snapshot.py`](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/scripts/create_daily_snapshot.py), com histórico rastreável via Git local e **sem qualquer push para repositórios remotos**.
