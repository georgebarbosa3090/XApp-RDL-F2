# Pacote LaTeX do Artigo Científico (Padrão SBRC / SBC)

Este diretório contém o artigo científico completo do projeto **xApp-RDL (Resource and Decision Layer) — Fase 2 (Context-Aware RDL)** formatado rigorosamente de acordo com os padrões da **Sociedade Brasileira de Computação (SBC)** para o **Simpósio Brasileiro de Redes de Computadores e Sistemas Distribuídos (SBRC)**.

---

## 📄 Estrutura de Arquivos

* [`main.tex`](main.tex): Documento principal em LaTeX contendo o artigo completo (Introdução, Fundamentação, Arquitetura, Modelagem MAPPO, Co-simulação ns-3/Near-RT RIC, Resultados Experimentais e Conclusão);
* [`sbc-template.sty`](sbc-template.sty): Pacote de estilo oficial da SBC/SBRC;
* [`sbc.bst`](sbc.bst): Arquivo de estilo de bibliografia BibTeX (padrão SBC);
* [`sbrc_references.bib`](sbrc_references.bib): Base de dados bibliográfica com referências (O-RAN Alliance, 3GPP, MAPPO, 5G-LENA, ns-O-RAN e literatura correlata);
* [`figures/`](figures/): Diretório autocontido com todas as figuras científicas de arquitetura, componentes e resultados em **tema claro (Light Theme)**;
* [`Makefile`](Makefile): Automação de compilação para Linux/macOS/WSL2;
* [`compile.bat`](compile.bat): Script de compilação em lote para Windows.

---

## 🛠️ Como Compilar

### Opção 1: Overleaf (Recomendado para Edição Colaborativa)
1. Compacte esta pasta `paper_sbrc` em um arquivo `.zip`;
2. No [Overleaf](https://www.overleaf.com), clique em **New Project** $\to$ **Upload Project** e selecione o arquivo `.zip`;
3. Defina o compilador como **pdfLaTeX** e compile diretamente.

### Opção 2: Linha de Comando (Linux / WSL2 / macOS com TeX Live)
```bash
cd paper_sbrc
make
```
ou manualmente:
```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

### Opção 3: Windows (com MiKTeX ou TeX Live instalado)
Execute o script no PowerShell ou Prompt de Comando:
```cmd
.\compile.bat
```

---

## 🖼️ Figuras de Arquitetura e Resultados em Tema Claro

O artigo utiliza as ilustrações científicas de alta resolução presentes em `figures/`:
1. **Pipeline Global e Near-RT RIC:** `figures/diagram_01_global_pipeline_architecture.png`
2. **Arquitetura Cognitiva e MAPPO CTDE:** `figures/diagram_02_arquitetura_cognitiva_mappo.png`
3. **Co-simulação Fim-a-Fim ns-3 + Kubernetes k3d:** `figures/cenario_3_arquitetura_cosimulacao_ns3_oran.png`
4. **Cenário 1 (EEVS - Energy vs QoS):** `figures/scenario_1_eevs_energy_vs_qos_light.png`
5. **Cenário 2 (TVS - Traffic Steering vs Slicing):** `figures/scenario_2_tvs_traffic_steering_slicing_light.png`
6. **Métricas Multidimensionais e CDFs:** `figures/cenario_4_comparativo_multidimensional_metricas.png`
7. **Throughput Celular e Jain Fairness:** `figures/cenario_5_vazao_throughput_e_jain_fairness.png`
8. **Latência de Decisão e Handover Ping-Pong:** `figures/cenario_6_latencia_decisao_e_estabilidade_handover.png`
9. **Dinâmica de Treinamento MAPPO e Safety Guards:** `figures/cenario_7_marl_treinamento_convergencia_perdas.png`
10. **Radar Holístico Multidimensional (3 Fases):** `figures/cenario_8_radar_comparativo_holistico_3fases.png`
