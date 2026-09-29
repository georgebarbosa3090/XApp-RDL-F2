# Volume 08: Estado da Arte (2020–2026) sobre Governança, Detecção e Mitigação de Conflitos Multi-xApp em O-RAN
## Evidências para as Hipóteses do XApp-RDL-F1 (H-RDL), Lacunas Científicas e Comparação Sistemática

> **Navegação da Documentação:**  
> **[Portal da Documentação](README.md)** | **[Vol 01: Arquitetura Core](01_arquitetura_e_modelagem.md)** | **[Vol 03: Taxonomia de Conflitos](03_taxonomia_de_conflitos_e_cenarios.md)** | **[Vol 04: Monografia Científica](04_relatorio_cientifico_mestre_rdl.md)** | **[Vol 21-F1: Demonstração Rica H-RDL](21_relatorio_demonstracao_rica_closed_loop_fase1_hrdl.md)**

---

### Metadados do Documento
- **Título Original:** Estado da Arte (2020–2026) sobre Governança, Detecção e Mitigação de Conflitos Multi-xApp em O-RAN
- **Autor Principal:** George Alexandro Ferreira Barbosa
- **Orientador:** Prof. Dr. André Riker
- **Instituição:** Universidade Federal do Pará (UFPA) — Instituto de Tecnologia (ITEC) — Programa de Pós-Graduação em Ciência da Computação (PPGCOMP)
- **Data da Síntese:** 27 de Setembro de 2026 (Atualizado em 29 de Setembro de 2026)
- **Documento PDF Oficial:** [`docs/assets/estado_arte_xapp_rdl_2020_2026.pdf`](assets/estado_arte_xapp_rdl_2020_2026.pdf) (SHA-256: `2c20d953c804f3d497b5f733d5780267448c758e769ef3b07235b1a7755f5a97`)

---

## Resumo Executivo

Este documento realiza uma revisão aprofundada da literatura entre 2020 e setembro de 2026 sobre coordenação, detecção, classificação, avaliação e mitigação de conflitos entre xApps no Near-RT RIC. A análise é orientada pelas hipóteses científicas do **XApp-RDL-F1 (H-RDL)**:
- **(H1) Redução de violações de SLA** com preservação de justiça ($J \ge 0,90$);
- **(H2) Supressão de oscilações temporais e ping-pong** ($\text{Churn} < 0,1\text{ ação/s}$, $t_{\text{settle}} < 200\text{ ms}$);
- **(H3) Overhead algorítmico sub-milissegundo** ($T_{\text{decision}} < 1,0\text{ ms}$);
- **(H4) Otimização segura por Safe-MAPPO** com bloqueio determinístico de ações inseguras ($\text{UnsafeApplied} \equiv 0$).

São cobertos trabalhos seminais sobre O-RAN programável e controle fechado, coordenação multiagente, frameworks formais de *Conflict Mitigation*, teoria dos jogos / barganha, gerenciamento de conflito *QoS-aware*, *profiling* pré-deployment, grafos de conflito GNN, *Digital Twins*, escalonadores adaptativos, validação OTA em testbed OTIC, destilação de políticas (*xApp distillation*) e métodos AI-native / LLM de 2026. A revisão evidencia que a literatura converge para a necessidade de uma **camada explícita de governança entre xApps**, mas ainda apresenta fragmentação entre segurança determinística, baixa latência, conflitos temporais, interoperabilidade E2 e adaptação aprendida — nicho científico preenchido pela arquitetura H-RDL / CA-RDL.

---

## 1. Escopo, Método de Busca e Critérios

A busca foi orientada a trabalhos publicados ou disponibilizados entre 2020 e 27 de setembro de 2026, com ênfase em periódicos e conferências IEEE, ACM, Elsevier (*Computer Networks*), Springer, ITU Journal, MDPI e preprints arXiv. Foram combinados grupos de consulta envolvendo: *O-RAN, xApp, Near-RT RIC, conflict mitigation, conflict management, multi-xApp, team learning, game theory, QoS-aware, traffic steering, energy saving, resource/power allocation, GNN conflict graph, digital twin, scheduler, OTA testbed, safe reinforcement learning, policy distillation, AI-native* e *generative agents*.

Foram incluídos trabalhos que satisfazem pelo menos um dos seguintes critérios:
1. Estabelecem a arquitetura de controle fechado e execução de xApps;
2. Identificam o risco de ações concorrentes ou objetivos antagônicos;
3. Propõem coordenação ou mitigação de conflitos;
4. Avaliam efeitos em QoS, throughput, energia, estabilidade, handover ou SLA;
5. Medem latência/viabilidade de execução dentro da janela do Near-RT RIC;
6. Tratam segurança, restrições, explicabilidade ou prevenção de ações inseguras.

---

## 2. Hipóteses do XApp-RDL-F1 Utilizadas como Eixo de Comparação

A fundamentação teórica e empírica do XApp-RDL-F1 estabelece as seguintes hipóteses de validação:

- **H1 — SLA e Justiça:** A H-RDL reduz a taxa de violação de SLA em pelo menos 30 pontos percentuais contra o baseline não coordenado, preservando equidade de Jain $J \ge 0,90$.
- **H2 — Estabilidade Temporal:** A H-RDL reduz o *Action Churn* para menos de $0,1\text{ ação/s}$ e atinge $t_{\text{settle}} < 200\text{ ms}$ em cenário de oscilação cíclica (*ping-pong*).
- **H3 — Sobrecarga Computacional:** O tempo algorítmico de decisão é estritamente sub-milissegundo ($T_{\text{decision}} < 1,0\text{ ms}$).
- **H4 — Segurança Aprendida:** Safe-MAPPO produz ganho de utilidade mantendo a barreira determinística $\text{UnsafeApplied} \equiv 0$.

O projeto posiciona a **H-RDL** como uma camada intermediária de governança no Near-RT RIC: intercepta propostas concorrentes, detecta conflitos, arbitra ações por modelo matemático determinístico, aplica *Safety Guards* físicos e somente então emite controle via E2SM-RC Format 1. A fase **CA-RDL** acrescenta contexto topológico, grafos de conhecimento causais e aprendizado por reforço seguro (Safe-MAPPO).

---

## 3. Evolução do Estado da Arte: 2020–2026

### 3.1. 2020–2021: Programabilidade, Closed-Loop e Nascimento do Problema de Coordenação
- **Bonati et al. (2021) [1]:** Apresentam a O-RAN como plataforma para loops de controle fechados (*closed-control loops*) programáveis e controle de RAN por xApps no Near-RT RIC. Base seminal para o XApp-RDL.
- **Rivera et al. (2020) [2]:** Propõem *multi-agent team learning* para a coordenação dos controladores O-RAN, explicitando que a desagregação e virtualização tornam inadequadas várias soluções clássicas de SON.
- **FlexRIC (Schmidt et al., 2021) [3]:** Demonstra SDK de Near-RT RIC com suporte a execução de múltiplos xApps e mensageria E2AP/E2SM em microssegundos.
- **ColO-RAN / OpenRAN Gym (Polese et al., 2023; Bonati et al., 2023) [4, 5]:** Viabilizam experimentação *closed-loop* em larga escala sobre testbeds PAWR/Colosseum.
- **Dryjański et al. (2021) [6]:** Demonstram implementação modular de *Traffic Steering* em O-RAN/6G.

### 3.2. 2022: Primeira Coordenação Explícita entre xApps Conflitantes
- **Zhang, Zhou e Erol-Kantarci (2022) [7]:** Formulam explicitamente o problema de conflitos entre xApps de fornecedores distintos e propõem *team learning* cooperativo para alocação de potência e blocos de rádio (PRB). Evidência direta para H1.
- **Kouchaki e Marojevic (2022) [8]:** Desenho e implantação de xApp de alocação de recursos baseado em *actor-critic*, reforçando a viabilidade de políticas aprendidas no Near-RT RIC.

### 3.3. 2023: Formalização da Taxonomia, CMF e Arbitragem Explícita
- **Adamczyk e Kliks (2023) [9]:** Propõem o *Conflict Mitigation Framework* (CMF) integrado ao Near-RT RIC, com detecção formal dos tipos direto, indireto e implícito definidos pelo O-RAN WG3. Antecedente arquitetural mais próximo da H-RDL.
- **Wadud, Golpayegani e Afraz (2023) [10]:** Introduzem sistema de conflito com barganha cooperativa (*Nash Social Welfare* e solução Eisenberg–Gale).

### 3.4. 2024: QoS-Aware, Profiling, Conflitos Convergentes e Grafos
- **QACM (Wadud et al., 2024) [11]:** Otimização *QoS-aware* que maximiza o número de xApps que mantêm seus requisitos de serviço atendidos sob conflito.
- **PACIFISTA (del Prever et al., 2025) [12]:** Avaliação preventiva de conflitos via *profiling* em sandbox, grafos hierárquicos e modelos estatísticos.
- **Corici et al. (2024) [13]:** Demonstram que o isolamento individual de funções é insuficiente e propõem gerenciamento convergente no plano de controle 6G. Evidência para H2.
- **Zolghadr et al. (2025) [14]:** Utilizam *GraphSAGE* (GNN) para reconstruir relações causais ocultas entre parâmetros de controle e KPIs. Antecedente direto da CA-RDL.

### 3.5. 2025: NDT, Schedulers, Testbed OTA, Causalidade e Produção
- **COMIX (Giannopoulos et al., 2025) [15]:** Combina CMF com *Network Digital Twin* (NDT) para avaliar ações concorrentes (potência vs eficiência energética) antes da aplicação física.
- **Cinemre e Mahmoodi (2025) [16]:** Propositor de escalonador adaptativo A2C para escolha dinâmica de xApps dependente do contexto.
- **Sultana et al. — OTIC (2025) [17]:** Validação experimental de CMF em testbed O-RAN OTIC com RF over-the-air (OTA), reportando redução de $78\%$ na variabilidade de throughput. Evidência externa para H2.
- **Sharma et al. (2025) [18]:** Avaliação de conflitos com SHAP, grafos acíclicos dirigidos (DAG) e inferência causal (ATE/CATE).

### 3.6. 2026: Distillation, AI-Native, Escalabilidade, Agentes Generativos e Interoperabilidade
- **xApp Distillation (Erdol et al., 2026) [19]:** Consolidação de políticas conflitantes em um modelo único via *knowledge distillation*.
- **Wadud et al. (2026) [20]:** Framework AI-powered com GNN, Bi-LSTM e SMOTE para detecção e classificação em escalas de 5 a 50 xApps.
- **ORIGAMI (Rahman et al., 2026) [21]:** Demonstração de mediação entre xApp de energia e xApp de throughput em testbed distribuído com interoperabilidade de componentes.
- **Salmi et al. (2026) [22]:** Arquitetura AI-native com motor de conflitos no Near-RT RIC e orquestração de intenções no Non-RT RIC.
- **Kurtulan et al. (2026) [23]:** Orquestrador ML-driven multi-xApp para redes 6G.
- **ORCA (Kwon e Zhang, 2026) [24]:** Agentes generativos com RAG e raciocínio simbólico para conflitos sob incerteza no Near-RT RIC.
- **Obiuwevwi et al. (2026) [25]:** Medições empíricas de inferência de IA em xApps sobre OAI/FlexRIC, comprovando tempos de execução na ordem de microssegundos a poucos milissegundos. Suporte a H3.
- **Safe RAN Slicing (Tuerxun e Nakao, 2026) [26]:** Demonstração de que o comportamento exploratório inseguro em RL convencional viola SLAs, exigindo Safe-RL. Suporte a H4.
- **Z2-ACT (Khowaja et al., 2026) [27]:** Controle agentic verificável e auditável para 6G RAN.

---

## 4. Tabela Comparativa Sistemática: Trabalhos Relacionados (2020–2026) vs XApp-RDL

### Tabela 1: Comparação Sistemática do Estado da Arte com XApp-RDL (F1/F2)

| Trabalho / Autor | Ano | Problema / Conflito | Método Proposto | Tipos de Conflito | Validação | Segurança Explícita | Latência / Tempo de Decisão | Relação com XApp-RDL |
| :--- | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **Rivera et al.** [2] | 2020 | Coordenação de agentes em O-RAN | Multi-agent team learning | Implícito / objetivos acoplados | Estudo / caso | Não | Não central | Antecede CA-RDL; não possui safety guards físicos. |
| **Bonati et al.** [1] | 2021 | Closed-loop e IA no Near-RT RIC | DRL / data-driven O-RAN | Não foca CM | Colosseum | Não | Near-RT | Base arquitetural para fechamento de malha. |
| **FlexRIC** [3] | 2021 | Execução programável multi-xApp | SDK Near-RT RIC / E2 | Não foca CM | Protótipo real | Não | $\mu\text{s}$ no monitor | Sustenta viabilidade temporal H3. |
| **Dryjański et al.** [6] | 2021 | Traffic Steering modular | xApp TS hierárquica | Mobilidade | Modular | Não | Near-RT | xApp canônica para cenários TS/TVS. |
| **Zhang et al.** [7] | 2022 | Potência vs Alocação PRB | Cooperative team DRL | Indireto | Simulação | Parcial | Não central | Evidência para H1; exige cooperação mútua. |
| **Kouchaki & Marojevic** [8]| 2022 | Alocação de Recursos | Actor-critic xApp | Não foca CM | Deploy E2 | Não | Near-RT | Base para agentes neurais isolados. |
| **Adamczyk & Kliks** [9] | 2023 | Conflitos intra-RIC | CMF + detecção dedicada | Direto, indireto, implícito | Simulação | Parcial | Near-RT | Mais próximo da H-RDL; H-RDL acrescenta guards e estabilidade temporal. |
| **Wadud et al.** [10] | 2023 | Configuração de parâmetros conflitantes | Barganha Nash / NSWF / EG | Direto / indireto | Teórico | Não | Não central | Fundamenta a arbitragem axiomática de Nash. |
| **QACM** [11] | 2024 | Preservação de QoS multi-xApp | Otimização QoS-aware | Direto, indireto, implícito | Simulação | Parcial | Não central | Sustenta H1; H-RDL foca em tempo real estrito (< 1 ms). |
| **Corici et al.** [13] | 2024 | Instabilidade no plano de controle | Framework convergente 6G | Multi-loop | Arquitetura | Parcial | Near-RT | Sustenta H2 e necessidade de governança centralizada. |
| **PACIFISTA** [12] | 2024/25 | Predição de conflitos pré-deploy | Profiling + grafos + estatística | Direto, indireto, implícito | Colosseum | Parcial | Pre-deploy | Complementar: atua pré-deployment, H-RDL atua em runtime. |
| **Zolghadr et al.** [14] | 2025 | Relações ocultas parâmetro-KPI | GraphSAGE (GNN) | Direto, indireto, implícito | WCNC / numérico | Não | Não central | Antecedente direto do módulo KG/GNN da CA-RDL. |
| **COMIX** [15] | 2025 | Throughput vs Energia / Potência | CMF + Network Digital Twin | Direto / indireto | Canal NR | Parcial | Avaliação prévia | Similar ao EEVS; H-RDL usa guard determinístico mais leve. |
| **Cinemre & Mahmoodi** [16] | 2025 | Escolha dinâmica entre xApps | Escalonador A2C | Indireto / contextual | Simulação | Não | Conceitual | Sustenta dependência de contexto da CA-RDL. |
| **Sultana et al. (OTIC)** [17] | 2025 | CMF em testbed físico | Detecção + mitigação de regras | Indireto / priorização | OTIC OTA RF | Parcial | Runtime | Evidência externa forte para H2 (-78% variabilidade). |
| **Sharma et al.** [18] | 2025 | Descoberta causal de conflitos | SHAP + DAG + ATE/CATE | Indireto / implícito | Modelagem | Não | Não central | Complementa a análise causal forense da RDL. |
| **xApp Distillation** [19] | 2026 | Eliminação de conflitos | Policy distillation | Multi-xApp | Simulação | Parcial | Near-RT | Alternativa de fusão; RDL preserva independência multi-vendor. |
| **Wadud et al. (AI-CM)** [20] | 2026 | Escala de 5 a 50 xApps | GNN / Bi-LSTM / SMOTE | Direto, indireto, implícito | ns-3 O-RAN | Não | Acelerado | Motiva a transição H-RDL (regras rápidas) para CA-RDL (IA em escala). |
| **ORIGAMI** [21] | 2026 | Energia vs Throughput | Mediação orientada a serviços | Antagônicos | Testbed dist. | Parcial | Runtime | Paralelo ao cenário canônico EEVS da H-RDL. |
| **Salmi et al.** [22] | 2026 | Coordenação AI-native + Intents | CME adaptativo + LLM Non-RT | Multi-xApp / rApp | Protótipo | Parcial | Near-RT | Direção futura para orquestração federada (Fase 3). |
| **Kurtulan et al.** [23] | 2026 | Conflitos multi-xApp em 6G | Orquestrador ML-driven | Multi-xApp | Experimental | Parcial | Real-time | Valida orquestração inteligente em tempo real. |
| **ORCA** [24] | 2026 | Conflitos sob incerteza | Agentes generativos + RAG | Implícito / desconhecido | INFOCOM | Parcial | Não focado | Raciocínio semântico sob incerteza. |
| **XApp-RDL (F1/F2)** | **2026** | **Slicing, QoS, Energia, TS, Churn e Safety** | **Fase 1: Determinística (Nash/EEVS/Guards)<br>Fase 2: Cognitiva (GNN/Safe-MAPPO)** | **Direto, Indireto, Implícito e Temporal** | **ns-3.48 + 5G-LENA + NORI + OSC RIC** | **SIM (Guards Invariantes $\text{Unsafe} \equiv 0$)** | **$0,118\text{ ms}$ (F1)<br>$0,34\text{ ms}$ (F2)** | **Integra segurança determinística desacoplada, supressão de churn, baixa latência e conformidade E2 completa.** |

---

## 5. Matriz de Aderência da Literatura às Hipóteses H1–H4

### Tabela 2: Grau de Aderência Conceitual dos Trabalhos às Hipóteses da RDL

| Trabalho | H1 (SLA / Ganho) | H2 (Estabilidade / Churn) | H3 (Latência < 1 ms) | H4 (Safety / Invariante) |
| :--- | :---: | :---: | :---: | :---: |
| Zhang et al. (2022) [7] | **Forte** | Média | Baixa | Baixa |
| Adamczyk & Kliks (2023) [9] | **Forte** | **Forte** | Média | Média |
| QACM (2024) [11] | **Forte** | Média | Baixa | Média |
| PACIFISTA (2025) [12] | **Forte** | **Forte** | Baixa | Média |
| COMIX (2025) [15] | **Forte** | Média | Média | **Forte** |
| Sultana et al. OTIC (2025) [17] | **Forte** | **Forte** | Média | Média |
| xApp Distillation (2026) [19] | **Forte** | **Forte** | Média | Média |
| Wadud et al. AI-CM (2026) [20] | **Forte** | **Forte** | Média | Baixa |
| ORIGAMI (2026) [21] | **Forte** | **Forte** | Média | Média |
| Obiuwevwi et al. (2026) [25] | Baixa | Baixa | **Forte** | Baixa |
| Safe RAN Slicing (2026) [26] | **Forte** | Média | Média | **Forte** |
| **XApp-RDL (Proposta)** | **DIRETA** | **DIRETA** | **DIRETA** | **DIRETA** |

---

## 6. Lacunas Científicas Identificadas e Contribuição Específica da H-RDL

A análise crítica da literatura revela cinco lacunas fundamentais que justificam a concepção do XApp-RDL:

1. **Lacuna 1 — Segurança Determinística Desacoplada da Política:**  
   Modelos de RL, GNN e heurísticas de utilidade podem convergir para ações subótimas ou instáveis durante transientes. A H-RDL introduz uma barreira invariante física desacoplada ($\text{UnsafeApplied} \equiv 0$), garantindo que comandos ilegais nunca cheguem à RAN, independentemente do algoritmo decisório.
2. **Lacuna 2 — Conflitos Temporais Tratados como Propriedade de Controle:**  
   A taxonomia clássica O-RAN foca em parâmetros estáticos (direto/indireto/implícito). A H-RDL formaliza o *conflito temporal* como dimensão de primeira classe, introduzindo métricas quantitativas de *Action Churn*, tempo de estabilização ($t_{\text{settle}}$) e histerese temporal (*cooling windows*).
3. **Lacuna 3 — Arquitetura de Dois Níveis (*Fast-Path* vs *Slow-Path*):**  
   Conciliação entre determinismo sub-milissegundo para conflitos frequentes ($T_{\text{dec}} = 0,118\text{ ms}$) na Fase 1 (H-RDL) e capacidade cognitiva profunda para cenários heterogêneos 5G-Adv/6G na Fase 2 (CA-RDL).
4. **Lacuna 4 — Fechamento Causal em Malha Fechada e Auditabilidade:**  
   Rastreamento ponta a ponta em 6 elos $KPM(t_0) \to \text{Decisão} \to \text{E2SM-RC} \to \text{ACK} \to \text{MAC} \to KPM(t_1)$ com hashes criptográficos SHA-256 e conformidade O-RAN WG3.
5. **Lacuna 5 — Preservação da Independência Multi-Vendor:**  
   Ao contrário de abordagens que exigem retreinamento conjunto (*team learning*) ou fusão de código (*distillation*), a RDL atua como árbitro externo neutro sobre a interface E2, compatível com xApps proprietárias (*black-box*).

---

## 7. Referências Bibliográficas

- **[1]** L. Bonati, S. D’Oro, M. Polese, S. Basagni, and T. Melodia, “Intelligence and learning in o-ran for data-driven nextg cellular networks,” *IEEE Communications Magazine*, vol. 59, no. 10, pp. 21–27, 2021.
- **[2]** P. E. I. Rivera, S. Mollahasani, and M. Erol-Kantarci, “Multi agent team learning in disaggregated virtualized open radio access networks (o-ran),” *IEEE Globecom Workshops*, 2020.
- **[3]** R. Schmidt, M. Irazabal, and N. Nikaein, “Flexric: an sdk for next-generation sd-rans,” in *Proc. of ACM CoNEXT*, 2021, pp. 411–425.
- **[4]** M. Polese, L. Bonati, S. D’Oro, S. Basagni, and T. Melodia, “Colo-ran: Developing machine learning-based xapps for open ran closed-loop control on programmable experimental platforms,” *IEEE Transactions on Mobile Computing*, vol. 22, no. 10, pp. 5787–5800, 2023.
- **[5]** L. Bonati, M. Polese, S. D’Oro, S. Basagni, and T. Melodia, “Openran gym: Ai/ml development, data collection, and testing for o-ran on pawr platforms,” *Computer Networks*, vol. 220, p. 109502, 2023.
- **[6]** M. Dryjański, Ł. Kułacz, and A. Kliks, “Toward modular and flexible open ran implementations in 6g networks: Traffic steering use case and o-ran xapps,” *Sensors*, vol. 21, no. 24, p. 8173, 2021.
- **[7]** H. Zhang, H. Zhou, and M. Erol-Kantarci, “Team learning-based resource allocation for open radio access network (o-ran),” in *IEEE ICC*, 2022, pp. 4938–4943.
- **[8]** M. Kouchaki and V. Marojevic, “Actor-critic network for o-ran resource allocation: xapp design, deployment, and analysis,” in *IEEE Globecom Workshops*, 2022.
- **[9]** C. Adamczyk and A. Kliks, “Conflict mitigation framework and conflict detection in o-ran near-rt ric,” *IEEE Communications Magazine*, vol. 61, no. 12, pp. 199–205, 2023.
- **[10]** A. Wadud, F. Golpayegani, and N. Afraz, “Conflict management in the near-rt-ric of open ran: A game theoretic approach,” in *IEEE Cybermatics*, 2023, pp. 479–486.
- **[11]** A. Wadud, F. Golpayegani, and N. Afraz, “Qacm: Qos-aware xapp conflict mitigation in open ran,” *IEEE Transactions on Green Communications and Networking*, vol. 8, no. 3, pp. 978–993, 2024.
- **[12]** P. B. del Prever, S. D’Oro, L. Bonati, M. Polese, M. Tsampazi, H. Lehmann, and T. Melodia, “Pacifista: Conflict evaluation and management in open ran,” *IEEE Transactions on Mobile Computing*, vol. 24, no. 10, pp. 10590–10605, 2025.
- **[13]** M. Corici, R. Modroiu, F. Eichhorn, E. Troudt, and T. Magedanz, “Towards efficient conflict mitigation in the converged 6g open ran control plane,” *Annals of Telecommunications*, vol. 79, pp. 621–631, 2024.
- **[14]** A. Zolghadr, J. F. Santos, L. A. DaSilva, and J. Kibiłda, “Learning and reconstructing conflicts in o-ran: A graph neural network approach,” in *IEEE WCNC*, 2025.
- **[15]** A. E. Giannopoulos, S. T. Spantideas, G. Levis, A. S. Kalafatelis, and P. Trakadas, “Comix: Generalized conflict management in o-ran xapps—architecture, workflow, and a power control case,” *IEEE Access*, vol. 13, pp. 116684–116700, 2025.
- **[16]** I. Cinemre and T. Mahmoodi, “xapp conflict mitigation with scheduler,” *arXiv preprint*, 2025.
- **[17]** A. Sultana, C. Adamczyk, M. R. Chowdhury, A. Kliks, and A. D. Silva, “Experimental evaluation of xapp conflict mitigation framework in o-ran: Insights from testbed deployment in otic,” in *IEEE INFOCOM Workshops*, 2025.
- **[18]** P. Sharma, S. Sun, S. Deshpande, A. Stavrou, and H. Wang, “Towards xapp conflict evaluation with explainable machine learning and causal inference in o-ran,” *arXiv preprint*, 2025.
- **[19]** H. Erdol, X. Wang, R. J. Piechocki, G. Oikonomou, and A. Parekh, “xapp distillation: Ai-based conflict mitigation in b5g o-ran,” *Computer Networks*, vol. 274, p. 111848, 2026.
- **[20]** A. Wadud, F. Golpayegani, and N. Afraz, “Ai-powered conflict management in open ran: Detection, classification, and mitigation,” *Computer Networks*, vol. 286, p. 112432, 2026.
- **[21]** M. A. Rahman, A. Duque, N. Chukhno, B. Niżnik, M. Gramaglia, and A. Garcia-Saavedra, “Conflict mitigation of xapps and interoperability of o-ran components: The origami approach,” in *EuCNC/6G Summit*, 2026, pp. 594–599.
- **[22]** S. Salmi, M. A. Ouameur, M. Bagaa, G. C. Alexandropoulos et al., “Ai-native o-ran architectures for 6g: Toward real-time adaptation, conflict resolution, and efficient resource management,” *IEEE Transactions on Network and Service Management*, vol. 23, pp. 4110–4121, 2026.
- **[23]** C. Kurtulan, O. Kalinagac, E. Ozdemir, B. Gorkemli, G. Karakus, S. Aktas, and M. Basaran, “Ml-driven network orchestrator for 6g o-ran: Resolving multi-xapp conflicts in near-rt ric,” *ITU Journal on Future and Evolving Technologies*, vol. 7, no. 2, pp. 145–159, 2026.
- **[24]** D. C. Kwon and X. Zhang, “Open ran conflict agents: Detecting and mitigating xapp conflicts with generative agents,” in *IEEE INFOCOM*, 2026, pp. 1–10.
- **[25]** L. Obiuwevwi, K. J. Rechowicz, S. Jayarathna, S. H. Bouk, F. Afrin, C. N. Barati, N. Moghim, V. Nannou, M. E. Rahman, and S. Shetty, “Enabling real-time ai in o-ran: Deploying and measuring ai inside a near-rt ric xapp,” *arXiv preprint*, 2026.
- **[26]** A. Tuerxun and A. Nakao, “Safe ran slicing in o-ran: Minimizing sla violations via model-based reinforcement learning,” in *IEEE CCNC*, 2026.
- **[27]** S. A. Khowaja, K. Dev, and G. C. Alexandropoulos, “Z2-act: End-to-end verifiable agentic intent control for open 6g ran,” *arXiv preprint*, 2026.
