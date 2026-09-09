# Relatório de Avaliação Estatística Rigorosa Multi-Semente (Modo: EXPERIMENT)

**Projeto:** xApp RDL (Resource and Decision Layer) — Governança Hierárquica Multi-Fase  
**Modo de Execução:** `EXPERIMENT` (Traces Empíricos Brutos ns-3)  
**Checksum do Dataset (SHA-256):** `bdfe34bbee5c456c4f38b2ed0640d0492f5dc27dace6b2bcc63949c5ce1268ba`  
**Ambiente:** ns-3 5G-LENA 3.5 GHz (n78) + Near-RT RIC  

## Tabela Comparativa de 3 Grupos com Intervalos de Confiança (IC 95%) e ANOVA

| Métrica Científica | Baseline (Sem RDL) | Fase 1: H-RDL | Fase 2: CA-RDL | Ganho Incr. (F2 vs F1) | ANOVA F-stat | ANOVA p-val | $\eta^2$ (Efeito) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Latência Média URLLC (ms)** | 11.74 ± 0.21 | 2.84 ± 0.03 | **2.12 ± 0.02** | **-25.6%** | `7781.1` | `< 0.001` | `0.994` |
| **Latência P99 URLLC (ms)** | 14.24 ± 0.39 | 3.14 ± 0.05 | **2.32 ± 0.03** | **-26.2%** | `3621.2` | `< 0.001` | `0.988` |
| **Violação de SLA URLLC (%)** | 100.00 ± 0.00 | 0.00 ± 0.00 | **0.00 ± 0.00** | **+0.0%** | `inf` | `< 0.001` | `1.000` |
| **Taxa de Conflitos (%)** | 34.67 ± 0.37 | 0.66 ± 0.06 | **0.00 ± 0.00** | **-100.0%** | `34936.3` | `< 0.001` | `0.999` |
| **Vazão Total Agregada (Mbps)** | 13.27 ± 0.15 | 33.89 ± 0.01 | **34.02 ± 0.00** | **+0.4%** | `77268.2` | `< 0.001` | `0.999` |
| **Packet Delivery Ratio (%)** | 38.93 ± 0.45 | 99.45 ± 0.02 | **99.83 ± 0.01** | **+0.4%** | `77268.2` | `< 0.001` | `0.999` |
| **Índice de Equidade de Jain** | 0.97 ± 0.00 | 1.00 ± 0.00 | **1.00 ± 0.00** | **+0.0%** | `545.9` | `< 0.001` | `0.926` |
| **Instabilidade Ping-Pong (ev/min)** | 21.92 ± 0.69 | 0.00 ± 0.00 | **0.00 ± 0.00** | **+0.0%** | `4219.2` | `< 0.001` | `0.990` |
| **Potência Média de Transmissão (dBm)** | 38.99 ± 0.08 | 33.48 ± 0.12 | **30.79 ± 0.10** | **-8.1%** | `6977.1` | `< 0.001` | `0.994` |
| **Tempo de Decisão RDL (ms)** | 0.00 ± 0.00 | 0.49 ± 0.01 | **4.27 ± 0.11** | **+3.78 ms** | `5768.2` | `< 0.001` | `0.993` |

## Conclusões da Validação Estatística (Computadas Dinamicamente)
1. **Rejeição da Hipótese Nula ($H_0$):** A ANOVA One-Way de 3 grupos confirma diferenciação estatisticamente significante ($p < 0.05$) em 10 de 10 métricas analisadas.
2. **Separação entre Ganho Global e Incremental:** A H-RDL fornece a base de contenção de conflitos e segurança de rádio, enquanto a CA-RDL adiciona coordenação contextual multiagente com ganho incremental de +0.0% no índice de Jain.
3. **Rastreabilidade e Integridade de Custódia:** O dataset possui hash SHA-256 `bdfe34bbee5c456c4f38b2ed0640d0492f5dc27dace6b2bcc63949c5ce1268ba` registrado em manifesto versionado em `experiments/results/experiment`.