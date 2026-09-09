# Relatório de Avaliação Estatística Rigorosa Multi-Semente (Modo: EXPERIMENT)

**Projeto:** xApp RDL (Resource and Decision Layer) — Governança Hierárquica Multi-Fase  
**Modo de Execução:** `EXPERIMENT` (Traces Empíricos Brutos ns-3)  
**Checksum do Dataset (SHA-256):** `c755ec622299f72ea241a1ce2aeaf973e7f84843d651844fc2c0d7c4a1f88655`  
**Ambiente:** ns-3 5G-LENA 3.5 GHz (n78) + Near-RT RIC  

## Tabela Comparativa de 3 Grupos com Intervalos de Confiança (IC 95%) e ANOVA

| Métrica Científica | Baseline (Sem RDL) | Fase 1: H-RDL | Fase 2: CA-RDL | Ganho Incr. (F2 vs F1) | ANOVA F-stat | ANOVA p-val | $\eta^2$ (Efeito) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Latência Média URLLC (ms)** | 11.74 ± 0.20 | 2.84 ± 0.03 | **2.12 ± 0.02** | **-25.6%** | `8911.1` | `< 0.001` | `0.995` |
| **Latência P99 URLLC (ms)** | 14.74 ± 0.49 | 3.20 ± 0.06 | **2.36 ± 0.04** | **-26.3%** | `2435.4` | `< 0.001` | `0.982` |
| **Violação de SLA URLLC (%)** | 100.00 ± 0.00 | 0.00 ± 0.00 | **0.00 ± 0.00** | **+0.0%** | `inf` | `< 0.001` | `1.000` |
| **Taxa de Conflitos (%)** | 34.67 ± 0.00 | 0.67 ± 0.00 | **0.00 ± 0.00** | **-100.0%** | `inf` | `< 0.001` | `1.000` |
| **Vazão Total Agregada (Mbps)** | 490.51 ± 5.62 | 1253.01 ± 0.28 | **1257.80 ± 0.08** | **+0.4%** | `77268.2` | `< 0.001` | `0.999` |
| **Packet Delivery Ratio (%)** | 38.93 ± 0.45 | 99.45 ± 0.02 | **99.83 ± 0.01** | **+0.4%** | `77268.2` | `< 0.001` | `0.999` |
| **Índice de Equidade de Jain** | 0.97 ± 0.00 | 1.00 ± 0.00 | **1.00 ± 0.00** | **+0.0%** | `545.9` | `< 0.001` | `0.926` |
| **Instabilidade Ping-Pong (ev/min)** | 22.00 ± 0.00 | 0.00 ± 0.00 | **0.00 ± 0.00** | **+0.0%** | `inf` | `< 0.001` | `1.000` |
| **Potência Média de Transmissão (dBm)** | 39.01 ± 0.00 | 33.89 ± 0.00 | **31.04 ± 0.00** | **-8.4%** | `inf` | `< 0.001` | `1.000` |
| **Tempo de Decisão RDL (ms)** | 0.00 ± 0.00 | 14.20 ± 0.00 | **12.50 ± 0.00** | **-1.70 ms** | `inf` | `< 0.001` | `1.000` |

## Conclusões da Validação Estatística (Computadas Dinamicamente)
1. **Rejeição da Hipótese Nula ($H_0$):** A ANOVA One-Way de 3 grupos confirma diferenciação estatisticamente significante ($p < 0.05$) em 10 de 10 métricas analisadas.
2. **Separação entre Ganho Global e Incremental:** A H-RDL fornece a base de contenção de conflitos e segurança de rádio, enquanto a CA-RDL adiciona coordenação contextual multiagente com ganho incremental de +0.0% no índice de Jain.
3. **Rastreabilidade e Integridade de Custódia:** O dataset possui hash SHA-256 `c755ec622299f72ea241a1ce2aeaf973e7f84843d651844fc2c0d7c4a1f88655` registrado em manifesto versionado em `experiments/results/experiment`.