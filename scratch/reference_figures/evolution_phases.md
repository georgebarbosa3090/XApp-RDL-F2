# Roadmap de Maturidade: xApp RDL

Conforme a estratégia de dividir a maturidade do projeto em três fases, este documento consolida a evolução da **Resource and Decision Layer (RDL)**, permitindo uma transição acadêmica e experimental segura. A primeira fase (implementada neste fork `iqos-xapp-rdl-phase1`) estabelece a base com um baseline determinístico.

## Fase 1 — RDL determinística e segura (Atual)
**Status:** Implementada no projeto atual (`H-RDL`).

O orquestrador resolve conflitos sem usar Multi-Agent Reinforcement Learning (MARL). A tomada de decisão utiliza:
- **Detecção:** Identifica as ações sobre os mesmos parâmetros ou ações com impactos correlacionados.
- **Regras Físicas (Safety Guard):** Limites de operação impostos antes da execução.
- **Heurística (Função de Utilidade Estática):**
  A ação selecionada \(a^* = \arg\max_{a\in A} U(a)\) é avaliada usando uma função de utilidade multiobjetivo:
  \(U(a) = w_1 SLA\_score + w_2 Throughput\_score + w_3 Energy\_score + w_4 Stability\_score + w_5 Priority\_score\)

Esta fase serve como o **baseline H0** para os experimentos.

---

## Fase 2 — RDL adaptativa orientada por contexto (Próximo Passo)
**Objetivo:** Uma heurística dinâmica e dependente de estado (**CA-RDL - Context-Aware RDL**).

Na Fase 2, a função de utilidade evolui de \(U(a) = f(a)\) para \(U(a|s) = f(a, s)\), onde \(s\) é o estado da rede com base nos KPMs:
\(s_t = [throughput, delay, SINR, PRB, load, energy, SLA]\)

### Principais Inovações
1. **Reuso Histórico com Similaridade:** Utiliza K-Nearest Neighbors (ou busca vetorial simples) no Histórico, avaliando `similarity(s, s_i)`.
2. **Recompensa Emulada:** A heurística de escolha refinará a utilidade gerando deltas estimados no estado, por exemplo:
   \(U(a,s) = w_T \Delta throughput(a,s) - w_L \Delta delay(a,s) - w_E \Delta energy(a,s) - w_S \Delta SLA(a,s)\)
3. **Criação de Dataset para MARL:** Cada decisão registrará \((s_t, a_t, r_t, s_{t+1})\). Isso criará os dados off-policy perfeitos para inicializar o treinamento da Fase 3 de maneira mais eficiente.

---

## Fase 3 — RDL cognitiva com MAPPO (Estado da Arte)
**Objetivo:** Hibridismo entre determinismo e MARL (**RDL-C - Cognitive MARL-enabled RDL**).

Somente na Fase 3, o `MAPPOCoordinator` (presente na concepção original do repositório) retorna para atuar cirurgicamente nos domínios complexos.

### Arquitetura Híbrida 
```text
                     Conflict
                        │
                        ▼
                ┌───────────────┐
                │ Classifier    │
                └───────┬───────┘
                        │
        ┌───────────────┼────────────────┐
        │               │                │
     trivial         direct         indirect/
        │               │            complex
        ▼               ▼                ▼
      Rule          Heuristic          MAPPO
        │               │                │
        └───────────────┬────────────────┘
                        │
                        ▼
                   Safety Guard
```

- **Trivial/Físico:** Anti-ping-pong, emergências, e validação de power range continuarão como Hard Policies (sem RL).
- **Conflito Indireto:** Aqui o MARL brilhará, inferindo sobre interações não lineares (e.g., uma xApp altera Power e outra Altera PRB simultaneamente) num espaço combinatório proibitivo para simples cálculos exaustivos da heurística CA-RDL.

### Modelo MAPPO
1. **Rede:** Centralized Critic, Decentralized Actors.
2. **Observação (\(o_i\)) / Estado (\(s_t\)):** Utiliza a mesma infraestrutura de telemetria construída para a Fase 2.
3. **Reward (\(R_t\)):** Usará os exatos scores desenvolvidos na Fase 2:
   \(R_t = 0.30T - 0.20D - 0.15E - 0.25V - 0.10C\)
4. **Safety Shield:** RL \(\rightarrow\) Safety Guard \(\rightarrow\) Execução ou Fallback heurístico.

---

### Experimentos / Artigo Final
Com essa estrutura modular de evolução, os experimentos podem comparar:
- **B0:** FCFS / sem coordenação
- **B1 (Fase 1):** RDL heurística H-RDL
- **B2 (Fase 2):** RDL contextual CA-RDL
- **B3 (Fase 3):** RDL + MAPPO (Hybrid Decision Engine)
- **B4 (Ablação):** MAPPO sem Safety Guard (só simulação)
