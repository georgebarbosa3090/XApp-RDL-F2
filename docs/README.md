# Portal de Documentação Técnica: xApp RDL (Fase 1 H-RDL & Fase 2 CA-RDL)

<div align="center">

**Resource and Decision Layer com Heurísticas Determinísticas, Aprendizado por Reforço Multiagente (MARL / MAPPO) e Governança Cognitiva**  
*Interoperabilidade com O-RAN ALLIANCE WG3, O-RAN SC (Release J), NORI (5G-LENA v5.1 / ns-3.48) e OpenRAN@Brasil Blueprint v3.*

</div>

---

### Navegação Multi-Fases do Projeto RDL (Resource and Decision Layer)

| Fase do Projeto | Descrição e Paradigma de Controle | Status de Implementação | Repositório Oficial |
| :---: | :--- | :---: | :---: |
| **Fase 1** | **RDL Determinística e Segura (H-RDL)**<br/>*Janela em lote (200ms), heurísticas TVS/EEVS, Safety Guards físicos e mapeamento formal E2AP/E2SM.* | **Implementada / Operacional** | [georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1) |
| **Fase 2 (Atual)** | **RDL Baseada em Contexto (CA-RDL)**<br/>*Aprendizado por Reforço Multiagente (MARL / MAPPO), observabilidade Service Mesh e cognição contextual 5G-A/6G.* | **Ativa / Em Evolução** | [georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2) |
| **Fase 3** | **RDL Autônoma e Federada 6G (Zero-Touch)**<br/>*Inteligência distribuída, orquestração por intenção (Intent-Driven) e coordenação Cross-Tier Non-RT / Near-RT / NTN.* | **Roadmap / Planejada** | *Em especificação futura* |

---

## 1. Estrutura Sequencial Completa dos 17 Volumes Técnicos

A documentação da **xApp RDL (Fase 1 & Fase 2)** está organizada em 17 volumes sequenciais contíguos (01 a 17):

```mermaid
graph TD
    subgraph S1["1. Arquitetura & Infraestrutura (01-04)"]
        V01["[Vol 01] Arquitetura Cognitiva & Formulação MAPPO"]
        V02["[Vol 02] Cluster k3d, Redis DBAAS & Rancher"]
        V03["[Vol 03] Deploy Helm & Kubernetes (OpenRAN@Brasil v3)"]
        V04["[Vol 04] Observabilidade Kiali, Prometheus & Injeção Mesh"]
    end

    subgraph S2["2. Simulação, Cenários & Validação (05-08)"]
        V05["[Vol 05] Testes de Simulação ns-3 & Benchmarks"]
        V06["[Vol 06] Cenários 5G, 5G-A e 6G (Massive MIMO & ISAC)"]
        V07["[Vol 07] Conformidade Normativa O-RAN WG3"]
        V08["[Vol 08] Proposta Arquitetural 6G Zero-Touch (Fase 3)"]
    end

    subgraph S3["3. Detalhamento Algorítmico & 6G (09-13)"]
        V09["[Vol 09] Relatório Técnico Detalhado Fase 2"]
        V10["[Vol 10] Matriz de Validade & Pontos de Atenção Fase 3"]
        V11["[Vol 11] RDL Autônoma & Federada 6G"]
        V12["[Vol 12] Resultados & Desempenho Comparativo Fase 2"]
        V13["[Vol 13] Avaliação Testbed UFPA PCT OpenRAN@Brasil"]
    end

    subgraph S4["4. Relatórios Científicos & Auditorias Formais (14-17)"]
        V14["[Vol 14] Validação Científica Completa H-RDL (Fase 1)"]
        V15["[Vol 15] Validação Extensa & Auditoria CA-RDL (Fase 2)"]
        V16["[Vol 16] Avaliação Experimental Baseline vs H-RDL"]
        V17["[Vol 17] Protocolo de Simulações Contínuas ns-3/NORI"]
    end

    V01 --> V02 --> V03 --> V04 --> V05 --> V06 --> V07 --> V08 --> V09 --> V10 --> V11 --> V12 --> V13 --> V14 --> V15 --> V16 --> V17
```

---

## 2. Índice dos Volumes Técnicos (01 a 17)

### Bloco 1: Fundamentação, Infraestrutura e Observabilidade (Volumes 01 a 04)
* **[Volume 01: Arquitetura e Modelagem Matemática](01_arquitetura_e_modelagem_matematica.md)**: Clean Architecture, formulação de observação canônica ($\mathbb{R}^{60}$), ator-crítico descentralizado (CTDE) e modelos de recompensa multiobjetivo.
* **[Volume 02: Infraestrutura de Cluster k3d e Rancher](02_infraestrutura_cluster_k3d_e_rancher.md)**: Topologias Single-Node (~450MB), Dual-Node (~900MB) e Multi-Node (~1.5GB) com mapeamento de portas O-RAN.
* **[Volume 03: Guia de Deploy Helm e Kubernetes](03_guia_deploy_helm_e_k8s.md)**: Implantação rápida via perfil OpenRAN@Brasil Blueprint v3 (`deploy/openran-br-v3/`) e Helm Chart oficial `v2.0.0`.
* **[Volume 04: Observabilidade Kiali e Injeção de Tráfego](04_observabilidade_kiali_e_injecao_trafego.md)**: Service Mesh Istio, métricas Prometheus em tempo real e visualização de topologia inter-xApps no Kiali.

### Bloco 2: Simulações ns-3, Cenários e Governança O-RAN (Volumes 05 a 08)
* **[Volume 05: Testes de Simulação ns-3 e Benchmarks](05_testes_simulacao_ns3_e_benchmarks.md)**: Co-simulação Closed-Loop via NORI, 5G-LENA v5.1 e execução de cenários C++.
* **[Volume 06: Cenários de Teste 5G, 5G-Advanced e 6G](06_cenarios_de_teste_5g_5ga_6g_e_requisitos.md)**: Cenários 1 a 5 (EEVS, TVS, Multi-Carrier Massive MIMO, 6G ISAC e Governança Cross-Tier).
* **[Volume 07: Relatórios de Conformidade e Governança O-RAN](07_relatorios_conformidade_e_governanca.md)**: Matriz de conformidade formal com padrões O-RAN Alliance e 3GPP.
* **[Volume 08: Proposta Arquitetural RDL Fase 3 (6G)](08_proposta_arquitetural_rdl_fase3.md)**: Arquitetura Cross-Tier Near-RT / Non-RT / NTN e gêmeos digitais.

### Bloco 3: Algoritmos Detalhados, Desempenho e Testbed (Volumes 09 a 13)
* **[Volume 09: Relatório Técnico Detalhado](09_relatorio_tecnico_detalhado_fase2.md)**: Detalhamento dos algoritmos cognitivos, agentes de refinamento com quarentena comportamental (*Anti-Rogue Shield*) e mapeamento E2AP.
* **[Volume 10: Matriz de Validade e Pontos de Atenção Fase 3](10_matriz_validade_e_pontos_de_atencao_fase3.md)**: Análise de riscos e viabilidade técnica para 6G Zero-Touch.
* **[Volume 11: RDL Autônoma e Federada 6G](11_rdl_autonoma_e_federada_6g.md)**: Aprendizado Federado distribuído e orquestração baseada em intenção (*Intent-Driven*).
* **[Volume 12: Relatório de Desempenho Comparativo](12_relatorio_resultados_e_desempenho_comparativo_fase2.md)**: Validação estatística multi-semente ($N=30$, IC 95%) e comparativos com a Fase 1.
* **[Volume 13: Avaliação no Testbed UFPA PCT OpenRAN@Brasil](13_relatorio_avaliacao_testbed_ufpa_pct_openran_brasil_rdl.md)**: Roteiro de integração e plano de testes físicos no testbed nacional.

### Bloco 4: Validações Científicas e Auditorias Formais (Volumes 14 a 17)
* **[Volume 14: Validação Científica Completa do H-RDL (Fase 1)](14_relatorio_validacao_cientifica_completa_hrdl_fase1.md)**: Validação técnica formal, auditoria dos 4 Gates O-RAN, suíte multi-semente $N=30$ e matriz comparativa.
* **[Volume 15: Validação Extensa e Auditoria da Fase 2 (CA-RDL)](15_relatorio_extenso_validacao_fase2_auditoria_e_resolucao_desafios.md)**: Resolução integral dos 6 eixos invariantes, formulação Safe-MARL MAPPO e gradiente lagrangiano.
* **[Volume 16: Avaliação Experimental Baseline vs H-RDL](16_relatorio_avaliacao_experimental_baseline_vs_hrdl.md)**: Análise aprofundada de ganhos de vazão, latência de cauda P99 e supressão de ping-pong.
* **[Volume 17: Simulações Contínuas ns-3 / 5G-LENA / NORI](17_relatorio_simulacoes_continuas_ns3_5glena_nori.md)**: Protocolos de execução em malha fechada E2AP/E2SM.

### Matriz Normativa e Catálogo Visual
* **[Matriz de Versões e Compatibilidade O-RAN](e2/version-matrix.md)**: E2AP v02.03, E2SM-KPM v03.00, E2SM-RC v01.03 e Release J.
* **[Fontes Normativas e Especificações](e2/specification-sources.md)**: Especificações de referência O-RAN WG3.
* **[Catálogo Temático de Figuras (docs/figures/README.md)](figures/README.md)**: 44 ilustrações científicas estruturadas em 300 DPI.

---

## 3. Trilhas de Leitura Recomendadas

| Perfil de Engenharia / Pesquisa | Sequência Sugerida |
| :--- | :--- |
| **Pesquisador de IA / MARL 6G** | [Volume 01](01_arquitetura_e_modelagem_matematica.md) $\rightarrow$ [Volume 06](06_cenarios_de_teste_5g_5ga_6g_e_requisitos.md) $\rightarrow$ [Volume 09](09_relatorio_tecnico_detalhado_fase2.md) $\rightarrow$ [Volume 11](11_rdl_autonoma_e_federada_6g.md) $\rightarrow$ [Volume 12](12_relatorio_resultados_e_desempenho_comparativo_fase2.md) $\rightarrow$ [Volume 15](15_relatorio_extenso_validacao_fase2_auditoria_e_resolucao_desafios.md) |
| **Engenheiro de Deploy e Infraestrutura** | [Volume 02](02_infraestrutura_cluster_k3d_e_rancher.md) $\rightarrow$ [Volume 03](03_guia_deploy_helm_e_k8s.md) $\rightarrow$ [Volume 04](04_observabilidade_kiali_e_injecao_trafego.md) $\rightarrow$ [Volume 13](13_relatorio_avaliacao_testbed_ufpa_pct_openran_brasil_rdl.md) |
| **Especialista em Simulação ns-3 / NORI** | [Volume 05](05_testes_simulacao_ns3_e_benchmarks.md) $\rightarrow$ [Volume 06](06_cenarios_de_teste_5g_5ga_6g_e_requisitos.md) $\rightarrow$ [Volume 16](16_relatorio_avaliacao_experimental_baseline_vs_hrdl.md) $\rightarrow$ [Volume 17](17_relatorio_simulacoes_continuas_ns3_5glena_nori.md) $\rightarrow$ [Matriz E2](e2/version-matrix.md) |
| **Arquiteto de Redes e Governança O-RAN** | [Volume 01](01_arquitetura_e_modelagem_matematica.md) $\rightarrow$ [Volume 07](07_relatorios_conformidade_e_governanca.md) $\rightarrow$ [Volume 08](08_proposta_arquitetural_rdl_fase3.md) $\rightarrow$ [Volume 10](10_matriz_validade_e_pontos_de_atencao_fase3.md) $\rightarrow$ [Volume 14](14_relatorio_validacao_cientifica_completa_hrdl_fase1.md) |


---

[Voltar para a Página Inicial (README.md)](../README.md)
