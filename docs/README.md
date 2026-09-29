# Portal de Documentação Oficial — Projeto xApp RDL (Resource and Decision Layer)

<div align="center">

**Arquitetura Unificada de Governança, Arbitragem de Conflitos Multi-xApp e Validação Causal em Open RAN**  
*Homologado para O-RAN ALLIANCE WG2/WG3, O-RAN SC Release J, ns-3.48 / 5G-LENA v5.1 e NORI E2 Agent*

</div>

---

## 📚 Estrutura Consolidada da Documentação (14 Volumes Canônicos)

A documentação do ecossistema de pesquisa **xApp-RDL** está estruturada e consolidada em **14 volumes canônicos**, cobrindo exaustivamente a **Fase 1 (H-RDL: Heurística / Determinística)**, a **Fase 2 (CA-RDL: Cognitiva / Safe-MAPPO / Two-Tier dApp)** e o **Roadmap 6G (Fase 3: Federada)**:

```
docs/
├── 01_arquitetura_e_modelagem.md                                # [Vol 01] Arquitetura Core, Agentes e Modelagem Matemática (F1/F2)
├── 02_guia_operacional_deploy_e_simulacao.md                    # [Vol 02] Deploy K8s/k3d, Helm, Observabilidade e Simulação ns-3
├── 03_taxonomia_de_conflitos_e_cenarios.md                      # [Vol 03] Taxonomia de Conflitos e Portfólio de Cenários (S0–S15)
├── 04_relatorio_cientifico_mestre_rdl.md                        # [Vol 04] Monografia Científica Mestre, Resultados e Estatística (F1 × F2)
├── 05_auditoria_e_conformidade_oran.md                          # [Vol 05] Auditoria Causal, Rastreabilidade SHA-256 e Normas O-RAN
├── 06_roadmap_e_pesquisa_futura_6g.md                           # [Vol 06] Roadmap 2026–2028, Fase 3 Federada 6G e Testbed UFPA
├── 07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md     # [Vol 07] Resultados da Simulação, Baselines (B0–B6) e Cenários (S0–S15)
├── 08_estado_da_arte_governanca_conflitos_xapp_rdl_2020_2026.md # [Vol 08] Estado da Arte (2020–2026) sobre Governança Multi-xApp
├── 09_protocolo_execucao_simulacoes_validacao_periodico.md      # [Vol 09] Protocolo Experimental para Validação em Periódico (IEEE TNSM)
├── 10_analise_profunda_e_plano_de_melhorias_estrategicas.md     # [Vol 10] Análise Profunda e Plano de Melhorias Estratégicas
├── 11_relatorio_experimental_ns3_flowmonitor_s0_s15.md           # [Vol 11] Relatório Técnico Experimental ns-3 FlowMonitor (S0–S15)
├── 12_relatorio_demonstracao_rica_closed_loop_fase1_hrdl.md     # [Vol 12] Relatório de Demonstração Rica Closed-Loop (H-RDL / Fase 1)
├── 13_relatorio_demonstracao_rica_closed_loop_fase2_cardl.md     # [Vol 13] Relatório de Demonstração Rica Closed-Loop (CA-RDL / Fase 2)
├── 14_plano_editorial_estrategico_matriz_publicacoes_2026_2028.md # [Vol 14] Plano Editorial Estratégico & Matriz de Publicações (2026–2028)
├── assets/                                                      # Diagramas de arquitetura, modelos visuais e PDFs auditáveis
├── auditoria/                                                   # Laudos de auditoria técnica, atas de homologação e pareceres
├── compliance/                                                  # Perfis de compatibilidade O-RAN congelados e contratos de sincronização
├── e2/                                                          # Definições ASN.1 e matrizes normativas E2AP/E2SM
└── figures/                                                     # Figuras científicas e gráficos em alta resolução (300 DPI)
```

---

## 🧭 Guia de Leitura por Perfil de Atuação

| Perfil de Interesse | Volumes Recomendados | Objetivo Principal |
| :--- | :--- | :--- |
| **Arquiteto O-RAN / Engenheiro de Software** | [Vol 01](01_arquitetura_e_modelagem.md), [Vol 05](05_auditoria_e_conformidade_oran.md), [Vol 12](12_relatorio_demonstracao_rica_closed_loop_fase1_hrdl.md) & [Vol 13](13_relatorio_demonstracao_rica_closed_loop_fase2_cardl.md) | Compreender os agentes cognitivos, codecs ASN.1 APER, envelopes dApp e conformidade normativa E2AP/E2SM. |
| **Operador de Infraestrutura / DevOps** | [Vol 02](02_guia_operacional_deploy_e_simulacao.md), [Vol 12](12_relatorio_demonstracao_rica_closed_loop_fase1_hrdl.md) & [Vol 13](13_relatorio_demonstracao_rica_closed_loop_fase2_cardl.md) | Provisionar clusters k3d, instalar pacotes Helm, executar demonstrações em tempo real e monitorar métricas Prometheus/Grafana. |
| **Pesquisador Científico / Avaliador Editorial** | [Vol 04](04_relatorio_cientifico_mestre_rdl.md), [Vol 07](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md), [Vol 08](08_estado_da_arte_governanca_conflitos_xapp_rdl_2020_2026.md), [Vol 09](09_protocolo_execucao_simulacoes_validacao_periodico.md), [Vol 11](11_relatorio_experimental_ns3_flowmonitor_s0_s15.md) & [Vol 14](14_plano_editorial_estrategico_matriz_publicacoes_2026_2028.md) | Analisar as evidências causais, tabelas completas de simulação, revisão bibliográfica (2020–2026), telemetria FlowMonitor e plano de publicações. |
| **Pesquisador 6G / Estrategista de IA** | [Vol 06](06_roadmap_e_pesquisa_futura_6g.md), [Vol 10](10_analise_profunda_e_plano_de_melhorias_estrategicas.md) & [Vol 13](13_relatorio_demonstracao_rica_closed_loop_fase2_cardl.md) | Explorar a evolução para Intent-Driven RIC (A1), federação multi-RIC, Safe-MAPPO e orquestração Two-Tier dApp. |

---

## 🚀 Resumo Executivo dos 14 Volumes Canônicos

### [Volume 01: Arquitetura do Sistema, Módulos Core e Modelagem Matemática](01_arquitetura_e_modelagem.md)
Apresenta o design da plataforma xApp-RDL sob Clean Architecture e DDD, os agentes especialistas (`PerceptionAgent`, `ReasoningAgent`, `RefinementAgent`), modelos analíticos físicos de rádio (Shannon com calibração 3GPP, filas $M/G/1$, modelo de consumo Earth Project) e formulação CMDP / Safe-MAPPO com *Safety Guards* invariantes e Action Masking.

### [Volume 02: Guia Operacional de Deploy, Simulação e Observabilidade](02_guia_operacional_deploy_e_simulacao.md)
Guia prático passo a passo para provisionamento de clusters Kubernetes leves com `k3d`, deploys via Helm e manifestos K8s, configuração do Rancher e Kiali, execução da suíte de co-simulação ns-3.48 / 5G-LENA / NORI e integração com o testbed físico GreenRAN da UFPA.

### [Volume 03: Taxonomia de Conflitos Multi-xApp e Portfólio de Cenários (S0 a S15)](03_taxonomia_de_conflitos_e_cenarios.md)
Classifica formalmente os 5 tipos de conflito em Open RAN (Direto, Indireto, Implícito/Semântico, Temporal Ping-Pong e Tempestade de Conflitos) e detalha a especificação técnica dos 16 cenários experimentais (de macrocélulas 5G canônicas a satélites NTN, pelotões V2X e segurança Zero-Trust).

### [Volume 04: Relatório Científico Mestre de Experimentos RDL (F1 H-RDL × F2 CA-RDL)](04_relatorio_cientifico_mestre_rdl.md)
Monografia científica exaustiva detalhando o protocolo experimental em 6 camadas, resultados de 167 fluxos reais FlowMonitor, comparações pareadas multi-seed (Wilcoxon $p < 0,001$, Cohen's $d_z > 4,0$), ablações cognitivas, sensibilidade da janela de decisão ($\Delta t_{win}$), tempos de recuperação ($t_{recover}$), registro de UE (45,8 ms) e a galeria completa de 25 figuras científicas (300 DPI) e 15 tabelas consolidadas CSV.

### [Volume 05: Relatório de Auditoria Técnico-Científica e Conformidade O-RAN](05_auditoria_e_conformidade_oran.md)
Documenta a superação da lacuna metodológica de prova causal, o fechamento do círculo de evidências de não-repúdio ($KPM(t_0) \to \dots \to KPM(t_1)$), verificação de integridade por checksums SHA-256 e conformidade com especificações O-RAN WG2, WG3 e nGRG.

### [Volume 06: Roadmap de Pesquisa (2026–2028), Fase 3 e RDL Autônoma 6G](06_roadmap_e_pesquisa_futura_6g.md)
Delineia a evolução do projeto em direção ao 6G Zero-Touch, detalhando a governança por intenção via interface A1, aprendizado federado multi-RIC, coordenação SAGIN (Space-Air-Ground) e cronograma da campanha experimental física no laboratório GreenRAN/UFPA.

### [Volume 07: Relatório Exaustivo de Resultados da Simulação (S0 a S15)](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md)
Apresenta o comparativo multidimensional completo cruzando os 7 baselines (B0 a B6) e os 16 cenários experimentais (S0 a S15), detalhando throughput, latência P95, violação de SLA, tempos de estabilização ($t_{\text{settle}}$), eficiência energética (EEVS), decomposição em 11 estágios do loop fechado e matriz de recomendações técnicas de uso H-RDL vs CA-RDL.

### [Volume 08: Estado da Arte (2020–2026) sobre Governança, Detecção e Mitigação de Conflitos Multi-xApp](08_estado_da_arte_governanca_conflitos_xapp_rdl_2020_2026.md)
Revisão sistemática aprofundada da literatura cobrindo 23 trabalhos seminais de 2020 a setembro de 2026 (team learning, CMF, QACM, PACIFISTA, COMIX, OTIC, xApp distillation, GNNs e AI-native/LLM), mapeamento direto das hipóteses H1–H4 e análise das 5 lacunas científicas preenchidas pelo ecossistema XApp-RDL. Documento PDF original disponível em [`docs/assets/estado_arte_xapp_rdl_2020_2026.pdf`](assets/estado_arte_xapp_rdl_2020_2026.pdf).

### [Volume 09: Protocolo Experimental e Guia de Execução de Simulações para Validação Total em Periódico](09_protocolo_execucao_simulacoes_validacao_periodico.md)
Guia metodológico detalhado para validação em periódicos IEEE (TNSM/TMC/JSAC), estabelecendo os 4 Gates Editoriais, diretrizes anti-sintéticas, causalidade estrita por sementes pareadas ($N=30$) e protocolos de auditoria criptográfica.

### [Volume 10: Análise Profunda e Plano de Melhorias Estratégicas](10_analise_profunda_e_plano_de_melhorias_estrategicas.md)
Diagnóstico arquitetural exaustivo estruturado em 6 eixos estratégicos de melhoria (Detecção de Conflitos, Inteligência Artificial, Modelagem Física, Governança O-RAN, Qualidade de Software e Evidências Experimentais).

### [Volume 11: Relatório Técnico Experimental e Rastreabilidade do ns-3 FlowMonitor](11_relatorio_experimental_ns3_flowmonitor_s0_s15.md)
Registro oficial exaustivo de nível de pacote extraído diretamente dos traces FlowMonitor XML gerados pelo simulador ns-3.48 / 5G-LENA / NORI, cobrindo os 16 cenários (S0 a S15) ordenados cronologicamente, matrizes de RF, dispersão de pacotes, jitter e governança determinística.

### [Volume 12: Relatório de Demonstração Científica Rica em Circuito Fechado — H-RDL (Fase 1)](12_relatorio_demonstracao_rica_closed_loop_fase1_hrdl.md)
Documento oficial da Fase 1 consolidando a governança determinística do H-RDL, comparativo empírico dos baselines B0 a B3, cenários canônicos S0 a S8, a cadeia causal forense em 6 elos ($KPM(t_0) \to \text{Decisão} \to \text{RC} \to \text{ACK} \to \text{MAC} \to KPM(t_1)$), estudo de ablação e a campanha estatística multi-semente $N=30$.

### [Volume 13: Relatório de Demonstração Científica Rica em Circuito Fechado — CA-RDL (Fase 2)](13_relatorio_demonstracao_rica_closed_loop_fase2_cardl.md)
Documento oficial consolidando os resultados empíricos da suíte operacional D1 a D5 e do inspetor visual dos 8 estágios cognitivos (Cenários A, B e C), comprovando a validação irrefutável dos Gates 1 a 4, conformidade ASN.1 APER WG3, envelopes dApp sub-1ms (O-RAN nGRG) e estabilidade de sinalização sob tempestade de conflitos.

### [Volume 14: Plano Editorial Estratégico & Matriz Exaustiva de Publicações (2026–2028)](14_plano_editorial_estrategico_matriz_publicacoes_2026_2028.md)
Planejamento de submissões decompondo o projeto em 6 manuscritos independentes (Paper 1 a Paper 6) direcionados para periódicos de alto impacto (IEEE TNSM, IEEE TCCN, IEEE Network, Elsevier Computer Networks, Nature Communications e SBRC 2027), eliminando redundâncias temáticas e assegurando reprodutibilidade total.

---

### [Trilha Especial: Auditoria Profunda e Estabilização Oficial](auditoria/AUDITORIA_PROFUNDA_INTEGRAL_CONSOLIDADA_2026.md)
Documento canônico oficial de conciliação formal pós-homologação da release `v1.2.0-certified`, atestando a superação definitiva dos gargalos metodológicos:
- **[Laudo de Auditoria Técnico-Científica Profunda e Consolidada (2026)](auditoria/AUDITORIA_PROFUNDA_INTEGRAL_CONSOLIDADA_2026.md)** *(Documento Oficial Homologado no Repositório)*

---

- **Autor:** George Alexandro Ferreira Barbosa  
- **Orientador:** Prof. Dr. André Riker  
- **Instituição:** Universidade Federal do Pará (UFPA) — Instituto de Tecnologia (ITEC) — PPGCOMP  
- **Release Oficial:** `v1.2.0-certified` | Homologação Setembro de 2026
