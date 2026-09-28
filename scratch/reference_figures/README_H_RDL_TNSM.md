# H-RDL Paper 1 — IEEE TNSM Q4/2026

Arquivos:
- `H_RDL_TNSM_Q4_2026.tex`: manuscrito principal em IEEEtran.
- `references_hrdl.bib`: bibliografia BibTeX.

## Decisão editorial de evidência
O plano editorial `docs/22_plano_editorial_estrategico_matriz_publicacoes_2026_2028.md` define o alvo Q4/2026, o título saneado e a fronteira de escopo do Paper 1. Contudo, os artefatos certificados anexados (manuscrito/dissertação) ainda sustentam apenas cinco sementes para o contraste B0–B3/B1–B3, com Wilcoxon bilateral exato `p=0.0625`, e registram N=30, ablação e escalabilidade 2–100 xApps como gates confirmatórios pendentes.

Por isso, o manuscrito foi escrito de forma conservadora:
- resultados N=5 são apresentados como **certified/descriptive**;
- N=30, ablação, packet-level CDF/P99, escalabilidade e decodificação E2 independente aparecem como **pre-submission gates**;
- o valor confirmado no recorte atual é `T_decision = 0.12 ms`;
- a decomposição temporal mais fina do plano editorial (inference/arbitration/pipeline/E2E) deve substituir o texto conservador apenas após reprodução em artefatos timestamped do release final.

## Escopo isolado do Paper 1
Inclui: H-RDL determinística, conflitos multi-xApp, TVS/EEVS, temporal memory/cooldown, Safety Guard, E2 closed loop, rastreabilidade e resultados B0–B3.

Não inclui como contribuição experimental: Knowledge Graph, GraphSAGE/GNN, Safe-MAPPO, CA-RDL, rApp/dApp multi-tier ou Fase 3.

## Compilação
No Overleaf ou TeX Live:

```bash
pdflatex H_RDL_TNSM_Q4_2026.tex
bibtex H_RDL_TNSM_Q4_2026
pdflatex H_RDL_TNSM_Q4_2026.tex
pdflatex H_RDL_TNSM_Q4_2026.tex
```

Antes da submissão final, substituir/confirmar os resultados pendentes com o release experimental congelado e revisar cada entrada BibTeX contra DOI/IEEE Xplore.
