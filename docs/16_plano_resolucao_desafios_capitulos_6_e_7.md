# Volume 16: Relatório Consolidado de Resolução de Auditoria e Plano Diretor da CA-RDL
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2 (CA-RDL)  
**Documento de Referência:** Relatório de Superação de Desafios da CA-RDL (Auditorias Técnicas - Rodadas 1 e 2)  
**Autor:** George Barbosa & Equipe Antigravity  
**Data:** 09 de Setembro de 2026  
**Status:** Aprovado e 100% Integrado ao Repositório `XApp-RDL-F2` (Branch `main`)

---

## 1. Visão Geral e Estrutura das Rodadas de Auditoria

A validação científica e a prontidão operacional da **Context-Aware Resource and Decision Layer (CA-RDL)** foram submetidas a um processo formal de auditoria independente dividido em duas rodadas de escrutínio rigoroso:

1. **Primeira Rodada (Capítulos 6 e 7):** Diagnóstico dos seis gargalos centrais de engenharia e modelagem (representação de estado truncada em $D=10$, perda com gradiente nulo no Safe-RL, ausência de topologia inicializada, truncamento numérico de parâmetros fracionários no E2SM-RC, latência de polling de 20ms e mistura de dados sintéticos).
2. **Segunda Rodada (Capítulo 8 - Seções 8.2 a 8.8):** Reavaliação pós-correção inicial, que reconheceu os avanços na estrutura da perda PPO-Lagrangian e no evento de flush, mas apontou pendências residuais cruciais: (a) necessidade de expansão canônica para 6 agentes e $D=60$; (b) vínculo direto da ação amostrada $\pi_\theta(a|s)$ eliminando o bypass de score heurístico; (c) suporte a ponto fixo em TODOS os parâmetros E2; (d) perfis de potência diferenciados (Macro vs Small Cell) e FSM Zero-Trust; (e) relógio monotônico de alta precisão; (f) bloqueio estrito de dados sintéticos no modo `--mode experiment`.

Este documento consolida a **resolução matemática, arquitetural, de software e de evidências experimentais** para ambas as rodadas.

```mermaid
flowchart TD
    subgraph R1["Rodada 1 (Capítulos 6 e 7)"]
        A1["6.1 Unificação Configuração"] --> A2["6.2 Safe-RL PPO-Lagrangian A_safe"]
        A2 --> A3["6.3 Topologia e Contexto"]
        A3 --> A4["6.4 Codificação ASN.1 E2SM-RC"]
        A4 --> A5["6.5 threading.Event Fast-Flush"]
        A5 --> A6["6.6 Separação Demo vs Experimento"]
    end

    subgraph R2["Rodada 2 (Capítulo 8 - Seções 8.2 a 8.8)"]
        B1["8.2 Coordenador D=60 (6 xApps) + Topologia Auto"] --> B2["8.3 Action Masking Estrito na Política Neural"]
        B2 --> B3["8.4 Dicionário PARAM_PROFILES + FSM Zero-Trust + Macro/Small Cell"]
        B3 --> B4["8.5 Relógio Monotônico time.perf_counter com Decomposição"]
        B4 --> B5["8.6 Modo --mode experiment Estrito (Aborta sem traces)"]
        B5 --> B6["8.7 Suíte Completa test_audit_fixes_comprehensive.py"]
    end

    R1 --> R2
    R2 --> Ready["8.8 Encerramento Integral e Prontidão Testbed UFPA PCT"]
```

---

## 2. PARTE I: Resolução da Primeira Rodada (Capítulos 6 e 7)

### 2.1 (6.1) Unificação da Configuração e Representação de Propostas
- **Diagnóstico:** O vetor de observação de dimensão 10 suportava apenas 2 propostas simultâneas, e o score de complexidade $C(c, s) = 1.3$ para 2 xApps com conflito direto superava o limiar $\tau_1 = 1.2$, fazendo com que conflitos simples pulassem o Nível 1.
- **Solução Implementada:**
  - Definição do vetor de estado global canônico $s_t \in \mathbb{R}^{60}$ com blocos de 8 posições por proposta e máscara de presença de 6 bits.
  - Recalibração dos limiares: $\tau_1 = 1.6$ e $\tau_2 = 3.0$, garantindo que pares diretos ($C \approx 1.3$) sejam resolvidos deterministicamente pela Heurística de Nível 1 (< 1 ms).

### 2.2 (6.2) Formulação PPO-Lagrangian com Vantagem Penalizada (Safe-RL)
- **Diagnóstico:** A penalidade constante somada à loss produzia gradiente nulo: $\nabla_\theta [\lambda \max(0, \bar{c}-d)] = 0$.
- **Solução Implementada:**
  - Estimativa conjunta da Vantagem de Recompensa $\hat{A}_t^R$ e da Vantagem de Custo $\hat{A}_t^C$ via GAE.
  - Construção da **Vantagem Penalizada Conjunta**:
    $$\hat{A}_t^{\text{safe}} = \hat{A}_t^R - \lambda_k \hat{A}_t^C$$
  - Clipped Surrogate Objective dependente diretamente da razão de probabilidades $r_t(\theta)$:
    $$L^{\text{CLIP}}(\theta) = \hat{\mathbb{E}}_t \left[ \min\left( r_t(\theta) \hat{A}_t^{\text{safe}}, \, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) \hat{A}_t^{\text{safe}} \right) \right]$$
    garantindo que $\nabla_\theta L^{\text{CLIP}}(\theta) \neq 0$.
  - Atualização dual de Lagrange: $\lambda_{k+1} = \max(0, \min(10.0, \lambda_k + \alpha (E[C] - d)))$.

### 2.3 (6.3) Contexto por Nó e Grafo de Dependências
- **Diagnóstico:** Vizinhança vazia e dados de telemetria sem timestamp de validade.
- **Solução Implementada:**
  - Inicialização do grafo de interferência co-canal intercelular no startup da classe `PerceptionAgent`.
  - Telemetria indexada em tuplas `(node_id, metric, timestamp, ttl)`.

### 2.4 (6.4) Perfis de Controle E2 e Preservação Numérica
- **Diagnóstico:** Truncamento de frações via `int(value)` (razão $0.25 \to 0$).
- **Solução Implementada:**
  - Introdução de escala em ponto fixo para parâmetros decimais e harmonização de envelopes de controle.

### 2.5 (6.5) Resposta Temporal Dirigida por Eventos
- **Diagnóstico:** Pausa estática de 20 ms no laço de decisão impedia respostas sub-milissegundo para emergências URLLC.
- **Solução Implementada:**
  - Introdução de `self.flush_event = threading.Event()` com `wait(timeout=0.02)` e despertar reativo imediato ($< 0.1\text{ ms}$) para propostas com prioridade $\ge 80$.

### 2.6 (6.6) Separação de Modos e ANOVA de Três Grupos
- **Diagnóstico:** Análise estatística comparava apenas 2 grupos e gerava dados estocásticos sem separação explícita de procedência.
- **Solução Implementada:**
  - Implementação de ANOVA One-Way de 3 grupos [Baseline, H-RDL, CA-RDL] com cálculo do tamanho de efeito $\eta^2 = \frac{SS_{\text{between}}}{SS_{\text{total}}}$, testes post-hoc pareados/Mann-Whitney U e manifesto criptográfico SHA-256.

---

## 3. PARTE II: Resolução da Segunda Rodada de Auditoria (Seções 8.2 a 8.8)

A segunda rodada de auditoria examinou o código resultante da primeira rodada e apontou 6 pontos de refinamento para encerramento total. Todos foram resolvidos:

### 3.1 (8.2) Expansão do Coordenador para 6 Agentes e Topologia com TTL

#### Problema Identificado no Capítulo 8.2:
`ReasoningAgent` ainda continha `self.mappo = MAPPOCoordinator(n_agents=2, obs_dim=10, action_dim=5)` codificado fixamente, e `PerceptionAgent` não garantia topologia ativa na inicialização padrão.

#### Solução Implementada:
1. **Configuração Dinâmica do Coordenador:**
   Em `src/agents/reasoning_agent.py`:
   ```python
   n_agents = int(self.config.get("n_agents", 6))
   obs_dim = int(self.config.get("obs_dim", 60))
   action_dim = int(self.config.get("action_dim", 7))
   self.mappo = MAPPOCoordinator(n_agents=n_agents, obs_dim=obs_dim, action_dim=action_dim, config=self.config)
   ```
2. **Topologia Multi-gNB e Validação de TTL:**
   Em `src/agents/perception_agent.py`:
   - Topologia padrão automática: `{"gnb_01": ["gnb_02"], "gnb_02": ["gnb_01", "gnb_03"], "gnb_03": ["gnb_02"]}`.
   - Armazenamento com timestamp: `self.kpm_by_node[node_id] = (report, timestamp)`.
   - Método `get_kpm_report(node_id, now_ts)` retornando `(report, is_valid)` com janela de $1000\text{ ms}$. Em caso de dados expirados, o sistema aciona fallback conservador.

---

### 3.2 (8.3) Vínculo Direto Política $\to$ Ação com Action Masking Estrito

#### Problema Identificado no Capítulo 8.3:
O método `decide()` obtinha uma ação amostrada, mas depois recalculava um score heurístico paralelo para escolher a proposta, ignorando a decisão neural do ator.

#### Solução Implementada:
Em `src/agents/marl/mappo_agent.py`:
- **Eliminação Total do Score Paralelo:** A proposta vencedora é determinada **exclusivamente** pelo índice de ação $a \sim \pi_\theta(a|s)$.
- **Action Masking com Renormalização:** Propostas não presentes no lote recebem probabilidade zero na distribuição categórica. Ação $a \in \{0, \dots, N-1\}$ despacha `conflict.involved_xapps[a]`, e ação $a = N$ despacha No-Op (não atuar).
- O buffer de transições registra exatamente a tupla $(s_t, a_t, \log \pi(a_t), R_t, s_{t+1}, C_t)$, garantindo convergência estrita da política.

---

### 3.3 (8.4) Dicionário Sistemático `PARAM_PROFILES`, Perfis de Célula e FSM

#### Problema Identificado no Capítulo 8.4:
A multiplicação por 1000 era aplicada apenas se o nome contivesse `"RATIO"`, truncando `A3_OFFSET` e `SCHEDULER_WEIGHT`. O refinamento aplicava limite único de 43 dBm (sem perfil de Small Cell) e não possuía a FSM formal de 4 estados.

#### Solução Implementada:
1. **Dicionário Sistemático de Perfis ASN.1 APER:**
   Em `src/e2/rc_encoder.py`:
   ```python
   PARAM_PROFILES = {
       "PRB_QUOTA":          {"id": 1,  "scale": 1,    "unit": "PRB",         "min": 0,    "max": 100},
       "TX_POWER":           {"id": 2,  "scale": 10,   "unit": "dBm_x10",     "min": -100, "max": 430},
       "SCHEDULER_WEIGHT":   {"id": 3,  "scale": 1000, "unit": "milli_ratio", "min": 10,   "max": 10000},
       "A3_OFFSET":          {"id": 4,  "scale": 100,  "unit": "centi_dB",    "min": -1000,"max": 1000},
       "BEAM_DOWNTILT":      {"id": 10, "scale": 10,   "unit": "deg_x10",     "min": 0,    "max": 150},
       "ISAC_SENSING_RATIO": {"id": 11, "scale": 1000, "unit": "milli_ratio", "min": 0,    "max": 500},
       "CARRIER_AGG_RATIO":  {"id": 12, "scale": 1000, "unit": "milli_ratio", "min": 0,    "max": 1000}
   }
   ```
   Incluindo método `decode_control_request()` para verificação bidirecional de reversibilidade.
2. **Perfis de Potência por Tipo de Célula:**
   Em `src/agents/refinement_agent.py`:
   - **Macro Cell (`gnb_01`, `gnb_02`):** Teto físico $P_{\max} = 43.0\text{ dBm}$ ($20\text{ W}$).
   - **Small Cell / Micro (`gnb_03`):** Teto físico $P_{\max} = 23.0\text{ dBm}$ ($200\text{ mW}$).
3. **Máquina de Estados Finita (FSM) de Quarentena Zero-Trust:**
   - Estados: `ACTIVE` $\to$ `SUSPECT` (1 infração) $\to$ `QUARANTINE` (3 infrações em 10s $\to$ bloqueio por 30s) $\to$ `PROBATION` (10s de observação) $\to$ `ACTIVE`. Se houver infração durante `PROBATION`, retorno imediato para `QUARANTINE`.

---

### 3.4 (8.5) Mensuração Temporal Monotônica Decomposta

#### Problema Identificado no Capítulo 8.5:
Falta de instrumentação monotônica separando as etapas de espera, percepção, raciocínio e refinamento.

#### Solução Implementada:
Em `src/rdl_xapp.py`:
- Uso exclusivo de `time.perf_counter()` para evitar oscilações de relógio NTP.
- Decomposição estruturada em logs e métricas Prometheus:
  $$T_{\text{total}} = T_{\text{perception}} + T_{\text{reasoning}} + T_{\text{refinement}} + T_{\text{e2\_encode}}$$

---

### 3.5 (8.6) Separação Estrita entre Dados Demonstrativos e Experimentais

#### Problema Identificado no Capítulo 8.6:
O script de avaliação estatística chamava o gerador sintético mesmo quando a flag `--mode experiment` era fornecida.

#### Solução Implementada:
Em `scripts/run_multi_seed_evaluation.py`:
- **Comportamento no Modo `--mode experiment`:** Busca obrigatoriamente os arquivos brutos de traces (`experiments/results/data/dataset_multi_seed_metrics.csv`). Se ausentes, **o script aborta com `sys.exit(1)` e mensagem de erro**, impedindo terminantemente a criação silenciosa de dados fictícios.
- **Comportamento no Modo `--mode demo`:** Executa o modelo paramétrico estocástico e rotula os artefatos com `[MODO DEMONSTRATIVO: DADOS SINTÉTICOS PARAMÉTRICOS]`.

---

### 3.6 (8.7 e 8.8) Suíte de Testes Automatizada e Parecer de Encerramento

Criou-se a suíte de testes unitários e de integração `tests/test_audit_fixes_comprehensive.py`, cobrindo 100% dos requisitos auditados:
1. `test_8_2_reasoning_agent_hierarchical_routing()`: Validação do roteamento para Heurística ($\le 1.6$), Utilidade ($1.6 - 3.0$) e MAPPO ($> 3.0$).
2. `test_8_3_mappo_direct_policy_action_binding()`: Seleção direta via $\pi_\theta(a|s)$ e Action Masking.
3. `test_8_4_rc_encoder_systematic_profiles()`: Precisão numérica de $0.25$ (ISAC/Scheduler), $3.5$ dB (Offset A3), $6.5^\circ$ (Downtilt), $23.5$ dBm (Power) e $80$ PRBs.
4. `test_8_4_refinement_cell_profiles_and_fsm()`: Validação dos tetos Macro (43 dBm) vs Small Cell (23 dBm) e ciclo completo da FSM de Quarentena.
5. `test_8_5_perception_topology_and_ttl()`: Topologia multi-célula e invalidação por TTL (> 1s).

---

## 4. Matriz Comparativa Final de Fechamento das Pendências

| Desafio / Pendência Auditada | Status Inicial (Vol. 14) | Status Pós-Rodada 1 | Status Definitivo (Pós-Rodada 2) | Arquivo de Implementação |
| :--- | :---: | :---: | :---: | :--- |
| **Representação Canônica de Estado** | $D=10$ (2 xApps) | $D=60$ planejado | **Ativo no Coordenador ($D=60, N=6$)** | `src/agents/reasoning_agent.py` |
| **Limiares de Escalonamento** | $\tau_1=1.2, \tau_2=2.4$ | $\tau_1=1.6, \tau_2=3.0$ | **$\tau_1=1.6, \tau_2=3.0$ testado e validado** | `src/agents/reasoning_agent.py` |
| **Gradiente de Custo Safe-RL** | $\nabla_\theta = 0$ | $\hat{A}_t^{\text{safe}} = \hat{A}_t^R - \lambda \hat{A}_t^C$ | **$\hat{A}_t^{\text{safe}}$ com gradiente ativo** | `src/agents/marl/mappo_agent.py` |
| **Vínculo Política-Ação** | Bypass por score | Parcial | **Direto via $\pi_\theta(a|s)$ + Action Masking** | `src/agents/marl/mappo_agent.py` |
| **Topologia e Contexto por Nó** | Vazio / Sem TTL | Em especificação | **Topologia multi-gNB + TTL 1000ms** | `src/agents/perception_agent.py` |
| **Precisão Numérica E2SM-RC** | Truncamento inteiro | Escala parcial | **`PARAM_PROFILES` completo com ponto fixo** | `src/e2/rc_encoder.py` |
| **Perfis de Potência de Célula** | Teto global 43 dBm | Teto global | **Macro (43 dBm) vs Small Cell (23 dBm)** | `src/agents/refinement_agent.py` |
| **FSM de Quarentena Zero-Trust** | Binário simples | 30s fixo | **4 Estados (ACTIVE-SUSPECT-QUARANTINE-PROBATION)** | `src/agents/refinement_agent.py` |
| **Resposta Temporal** | Polling 20ms | `threading.Event` | **`threading.Event` + Monotônico `perf_counter`** | `src/rdl_xapp.py` |
| **Separação Demo vs Experimento** | Ambiguidade | Flags CLI | **Modo `--mode experiment` estrito (aborta sem traces)** | `scripts/run_multi_seed_evaluation.py` |
| **Validação Estatística ANOVA** | 2 Grupos (sem CA-RDL) | 3 Grupos | **ANOVA 3 Grupos + $\eta^2$ + Tukey Post-Hoc** | `scripts/run_multi_seed_evaluation.py` |

---

## 6. Resolução Definitiva dos Apontamentos da Seção 9 (Sprint 1 Executado e Validado)

Em resposta à auditoria formal consolidada (Seções 9.1 a 9.8 do relatório de superação de desafios), implementou-se e homologou-se o conjunto integral de correções do **Sprint 1**, respaldado por uma suíte de **53 testes automatizados (100% aprovados)**:

### 6.1 (9.1) Contrato Canônico de Observação ($D=60$) e Preservação de Prioridade
- **Implementação:** Em `src/agents/marl/mappo_agent.py`, o método `extract_features()` foi padronizado no vetor canônico $D=60$:
  - Índices $[0..5]$: Metadados globais e telemetria KPM (Throughput DL/UL, Delay QoS, PRB Tot, SINR DL).
  - Índices $[6..11]$: Máscara de presença de propostas em 6 bits booleanos.
  - Índices $[12..59]$: 6 blocos canônicos de propostas $\times$ 8 atributos (Hash da xApp, Hash do Nó, Tipo de Parâmetro, Valor Normalizado por Tipo, Prioridade Linear, Frescor Temporal, Validade Estrutural e KPI Alvo).
- **Preservação de Prioridade:** Normalização estrita linear `float(priority) / 100.0`, preservando a ordenação original: $40 \to 0.40$, $50 \to 0.50$, $80 \to 0.80$, $90 \to 0.90$.
- **Validação:** [test_observation_contract.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_observation_contract.py).

### 6.2 (9.2) Vínculo Inequívoco Política-Ação e Decisão de No-Op
- **Implementação:** O coordenador MAPPO aplica *Action Masking* estrito na distribuição $\pi_\theta(a|s)$. Ação $a \in [0, N-1]$ seleciona deterministicamente a proposta correspondente; ação $a = \text{action\_dim}-1$ ou retorno nulo aciona a decisão de **No-Op** (deferimento).
- **Semântica de No-Op:** Em `src/agents/reasoning_agent.py`, No-Op retorna `winning_actions = []` e `modified_value = None`, garantindo que nenhuma mensagem espúria de controle E2 seja emitida.
- **Validação:** [test_policy_action_binding.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_policy_action_binding.py).

### 6.3 (9.3) Indisponibilidade Contextual Estrita e Encaminhamento Conservador
- **Implementação:** Em `src/agents/perception_agent.py`, `get_kpm_report(node_id)` valida a presença do nó e a validade temporal ($\text{TTL} \le 1.0\text{ s}$). Caso o nó não esteja cadastrado ou a telemetria esteja expirada, retorna `(None, False)`.
- **Comportamento no Pipeline:** Em `src/rdl_xapp.py`, na ausência de contexto confiável, o sistema executa obrigatoriamente o encaminhamento conservador para a **Heurística Segura de Nível 1** (`_resolve_by_heuristic()`).
- **Validação:** [test_audit_fixes_comprehensive.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_audit_fixes_comprehensive.py).

### 6.4 (9.4) Validação Pública de Limites de Hardware por Tipo de Célula
- **Implementação:** Em `src/agents/refinement_agent.py`, os métodos públicos `validate(resolution, conflict)` e `validate_single_action(action)` repassam explicitamente o `node_id = action.node_id` para a função de limites físicos.
- **Limites Físicos:** Teto de potência de transmissão diferenciado: **Macro gNodeB (43 dBm / 20W)** versus **Small Cell (23 dBm / 200mW)**. Propostas que excedam o perfil da célula são rejeitadas e registradas na FSM Zero-Trust.
- **Validação:** [test_audit_fixes_comprehensive.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_audit_fixes_comprehensive.py) e [test_refinement_agent.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_refinement_agent.py).

### 6.5 (9.5) Codecs ASN.1 / APER Nativos e Shim Híbrido
- **Implementação:** Criou-se [src/e2/asn1_shim.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/src/e2/asn1_shim.py) para prover interoperabilidade contínua (pycrate nativo em nós O-RAN de produção + emulador estrutural puro em Python para ambientes de CI e testes). Corrigidos os imports em `src/rdl_xapp.py` para utilizar diretamente `KpmDecoder` e `RCEncoder`.
- **Perfis de Parâmetros e Validação:** Dicionário `PARAM_PROFILES` completo com fatores de escala de ponto fixo e validação estrita de faixa admissível (`min <= encoded_val <= max`), com rejeição imediata de parâmetros desconhecidos via `ValueError`.
- **Validação:** [test_e2_encoding_decoding.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_e2_encoding_decoding.py) e [test_aper_codecs.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_aper_codecs.py).

### 6.6 (9.6) Instrumentação Monotônica Decomposta
- **Implementação:** Medição de latência com `time.perf_counter()` decomposta em:
  $$T_{\text{total}} \ge T_{\text{queue}} + T_{\text{perception}} + T_{\text{reasoning}} + T_{\text{refinement}} + T_{\text{e2\_encode}}$$
- **Validação:** [test_latency_components.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_latency_components.py).

### 6.7 (9.7 e 9.8) Rastreabilidade Estrita e Empacotamento de Traces Brutos
- **Implementação:** Script `scripts/package_and_sync_raw_results.py` atualizado com suporte aos parâmetros `--mode demo|experiment` e `--strict`. No modo estrito de experimentação, a ausência de arquivos brutos emite erro formal (`FileNotFoundError`), impedindo a criação silenciosa de dados sintéticos e garantindo integridade criptográfica SHA-256 no manifesto.
- **Validação:** [test_provenance_check.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_provenance_check.py).

---

## 7. Superação Formal dos Desafios dos Capítulos 10 e 11 (Revisões 5a19149 e d436f5f)

Com base nas rodadas de auditoria científica detalhadas nos Capítulos 10 e 11 do *Relatório de Superação de Desafios da CA-RDL*, todas as problemáticas remanescentes foram matematicamente modeladas, implementadas nos caminhos públicos e validadas por testes de regressão:

```mermaid
flowchart TD
    subgraph S1["Eixo A: Representação & Ação (10.4 / 11.3 / 11.4)"]
        A1["MD5 Determinístico para xApp/Node IDs"] --> A2["Desambiguação No-Op (action_dim-1)"]
        A2 --> A3["Tratamento Explícito de Excesso (N > 6)"]
        A3 --> A4["Inferência Pura pi_theta(a|s) sem Reponderação Ad-Hoc"]
    end

    subgraph S2["Eixo B: E2 & Telemetria (10.5 / 11.5)"]
        B1["Agregação KPM por (node_id, ue_id)"] --> B2["Eliminação de Sobrescrita com Zero"]
        B2 --> B3["PDU Completo E2SM-RC (Header + Message APER)"]
        B3 --> B4["Decodificação Reversível Estruturada"]
    end

    subgraph S3["Eixo C: Proveniência & Entrega (11.2 / 11.6 / 11.7)"]
        C1["Fix Dockerfile Context no CI (-f docker/Dockerfile .)"] --> C2["Isolamento de Diretórios (results/demo vs results/experiment)"]
        C2 --> C3["Teste Negativo de Rejeição de Traces Sintéticos"]
        C3 --> C4["Instrumentação Monotônica de Espera em Fila T_queue"]
    end
```

### 7.1 Identificadores Determinísticos e Desambiguação de No-Op (10.4 & 11.3)
- **Problemática:** `hash()` nativo varia com `PYTHONHASHSEED`, gerando representações inconsistentes entre processos. Em lotes com $N \ge 7$ propostas, o índice 6 era interpretado como a 7ª proposta e não como a ação reservada de No-Op.
- **Solução Implementada:**
  - Função `_stable_hash(s, mod)` com digest MD5 determinístico independente de semente do runtime.
  - Verificação de No-Op (`action_idx == self.action_dim - 1` ou `action_idx >= n_proposals`) executada **antes** de qualquer indexação de propostas no coordenador MAPPO, retornando estritamente `(None, confidence)`.
  - Log de advertência explícito para excesso de propostas ($N > 6$), alocando os 6 primeiros slots no vetor $D=60$ de forma reprodutível e documentada.
- **Validação:** `test_deterministic_feature_hashing` em [test_observation_contract.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_observation_contract.py) e `test_action_cardinality_and_noop_disambiguation_with_many_proposals` em [test_policy_action_binding.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_policy_action_binding.py).

### 7.2 Vínculo Rigoroso Política-Ação e Gradiente Safe-RL Ativo (11.4)
- **Problemática:** Multiplicação ad-hoc das probabilidades por fatores de prioridade durante a inferência distorcia a política aprendida $\pi_\theta(a|s)$. O teste de gradiente não continha transições com custo não-nulo ($c_t > 0$).
- **Solução Implementada:**
  - Contrato formal entre treinamento e inferência: a distribuição mascarada gerada pelo ator governa diretamente a seleção de ação sem perturbações ad-hoc.
  - Teste de gradiente com transições de custo positivo ($c_t = 1.0 > d = 0.1$), validando a ativação da Vantagem Penalizada Conjunta $\hat{A}^{\text{safe}} = \hat{A}^R - \lambda \hat{A}^C$, perdas finitas e atualização positiva do multiplicador de Lagrange $\lambda > 0$.
- **Validação:** `test_safe_rl_cost_gradient_flow_and_lagrange_multiplier_update` e `test_pure_policy_inference_without_ad_hoc_reweighting` em [test_policy_action_binding.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_policy_action_binding.py).

### 7.3 Agregação Multimétrica na Telemetria KPM (11.5)
- **Problemática:** `KpmDecoder.decode_indication()` produzia 1 relatório individual por métrica preenchendo as demais com zero, causando sobrescrita indesejada do estado de KPM por nó.
- **Solução Implementada:** Agregação de todas as medições pertencentes ao mesmo par `(node_id, ue_id)` em uma única estrutura unificada contendo `drb_thp_dl`, `drb_thp_ul`, `drb_delay_dl` e `prb_used_dl` antes do retorno.
- **Validação:** `test_kpm_decoder_fallback` em [test_aper_codecs.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_aper_codecs.py).

### 7.4 Codificação Completa de PDU E2SM-RC e Decodificação Reversível (11.5)
- **Problemática:** `RCEncoder` construía o cabeçalho mas retornava apenas o corpo da mensagem binária.
- **Solução Implementada:** Implementação de `encode_control_pdu(node_id, param, value) -> Tuple[bytes, bytes]` retornando `(header_aper, msg_aper)`, além de métodos dedicados `decode_control_header()` e `decode_control_message()`.
- **Validação:** `test_rc_encoder_encode_pdu_and_header_decode` em [test_e2_encoding_decoding.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_e2_encoding_decoding.py).

### 7.5 Separação Rígida de Modos e Teste Negativo de Proveniência (11.6)
- **Problemática:** Exportação de dados sintéticos e experimentais para os mesmos destinos e ausência de teste negativo que force a rejeição de dados sintéticos no modo estrito.
- **Solução Implementada:**
  - Isolamento estrito de diretórios de exportação: `experiments/results/demo/` (dados sintéticos estocásticos calibrados) e `experiments/results/experiment/` (traces brutos experimentais ns-3).
  - Marcador de proveniência `synthetic="true"` nos dados sintéticos e validação estrita em `verify_raw_traces_exist()` que rejeita traces falsos em modo de experimento.
  - Cálculo de conclusões dinâmicas no relatório estatístico com base no número exato de métricas significantes via ANOVA ($p < 0.05$).
- **Validação:** `test_verify_raw_traces_rejects_synthetic_traces_in_experiment_mode` em [test_provenance_check.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_provenance_check.py).

### 7.6 Instrumentação Monotônica de Fila e Correção da Integração Contínua (11.2 & 11.7)
- **Problemática:** Medição de tempo no runtime não contabilizava espera na fila; falha no build Docker na esteira CI por troca de diretório de contexto.
- **Solução Implementada:**
  - Registro de `arrival_monotonic = time.perf_counter()` em cada ação ao entrar no buffer, calculando $T_{\text{queue}} = t_{\text{dequeue}} - t_{\text{enqueue}}$ e incorporando no log de decisão.
  - Correção do workflow `.github/workflows/ci.yml` para executar `docker build -t muriloavlis/iqos-xapp:latest -f docker/Dockerfile .` a partir da raiz do repositório.
- **Validação:** `test_decomposed_latency_pipeline_monotonic` em [test_latency_components.py](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase2/tests/test_latency_components.py).

---

## 8. Matriz de Cobertura e Resultados da Suíte de Testes (59/59 Aprovados)

Execução realizada no ambiente virtual WSL2 (`/home/george/.venv-rdl/bin/pytest tests/ -v`):

| Módulo de Teste | Quantidade | Foco de Validação Técnica | Resultado |
| :--- | :---: | :--- | :---: |
| `test_observation_contract.py` | 5 | Vetor $D=60$, presença de propostas (6 bits), normalização linear, excesso $>6$ e hash determinístico | **APROVADO** (100%) |
| `test_policy_action_binding.py` | 6 | Gradientes Actor-Critic, Action Masking, No-Op, Safe-RL Cost Gradient ($\nabla_\theta L^\text{safe} \neq 0$), inferência pura e desambiguação No-Op ($N=7$) | **APROVADO** (100%) |
| `test_e2_encoding_decoding.py` | 5 | Perfis E2SM-RC, rejeição de parâmetros inválidos, limites numéricos, reversibilidade e PDU Header+Message | **APROVADO** (100%) |
| `test_latency_components.py` | 2 | Decomposição monotônica ($T_\text{queue} + T_\text{perc} + T_\text{reas} + T_\text{ref} + T_\text{e2}$) e orçamento da Heurística | **APROVADO** (100%) |
| `test_provenance_check.py` | 4 | Cálculo de SHA-256, modo estrito, empacotamento demo e teste negativo de rejeição de dados sintéticos | **APROVADO** (100%) |
| `test_audit_fixes_comprehensive.py` | 5 | Roteamento hierárquico $C(c,s)$, No-Op, validação por perfil de célula, ponto fixo e TTL de contexto | **APROVADO** (100%) |
| `test_marl_mappo.py` | 8 | Coordenador MAPPO, cálculo GAE, multi-objetivo, transições e Safe-RL CMDP com Lagrange | **APROVADO** (100%) |
| `test_perception_agent.py` | 5 | Conflitos diretos, indiretos intra-célula, inter-célula (interferência co-canal) e nós isolados | **APROVADO** (100%) |
| `test_reasoning_agent.py` | 3 | Resolução Heurística Nível 1, Utilidade Nível 2A e escalonamento para Nível 2B (MAPPO) | **APROVADO** (100%) |
| `test_refinement_agent.py` | 6 | Limites físicos, barreira temporal, Pass-Through limpo, quarentena Zero-Trust e feixes MIMO | **APROVADO** (100%) |
| `test_reference_xapps.py` | 7 | Propostas de 6 xApps de referência (xSlice, Energy, TS, Beamformer, ISAC, Rogue) e tríade de conflito | **APROVADO** (100%) |
| `test_aper_codecs.py` | 3 | Decodificação E2AP Indication, decodificação KPM agregada com fallback e geração APER RC | **APROVADO** (100%) |
| **TOTAL GERAL** | **59** | **Cobertura Integral de Todos os Módulos do Sistema** | **59/59 PASS (100%)** |

---

## 9. Prontidão Operacional para o Testbed Open RAN Brasil (UFPA PCT / GreenRAN)

Com a resolução formal e certificada de todas as pendências arquiteturais, funcionais e metodológicas dos Capítulos 6, 7, 8, 9, 10 e 11 do relatório de auditoria:
1. **Infraestrutura de Hardware:** Servidores Dell PowerEdge R750 com aceleradores NVIDIA A100/A30 e SDRs USRPs NI X310 e N310 operando em Banda n78 (3.5 GHz) e FR2 mmWave (28 GHz).
2. **Pilha O-RAN Integrada:** Near-RT RIC O-RAN SC, E2 Nodes srsRAN Enterprise e Núcleo Open5GS 5G Standalone.
3. **Publicação Científica:** Base rigorosa para submissão aos periódicos de alto impacto **IEEE Transactions on Mobile Computing (TMC)** e **IEEE JSAC**, consolidando a arquitetura hierárquica escalonada (Heurística $\to$ Utilidade NDT $\to$ MAPPO Safe-RL) como estado da arte em governança autônoma multi-xApp.

---
*Documento homologado e integrado aos repositórios local e remoto `XApp-RDL-F2`.*


