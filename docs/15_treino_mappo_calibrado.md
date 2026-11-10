# 15 — Treino do MAPPO no ambiente calibrado (2026-11-10)

## 1. Desenho

| Item | Valor |
| :-- | :-- |
| Ambiente | `cardl/marl/env.py`: CMDP com 2 agentes (teto de PRB da fatia crítica e da fatia eMBB), 96 janelas por episódio (perfil diário de demanda: baixa à noite) |
| Propostas por janela | RANSlicer (teto que atende a demanda com 10 % de margem; prioridade 90 na crítica, 70 na eMBB), EnergySaver (60 % do necessário, prioridade 65), Rogue (150 %, 10 % das janelas) |
| Resposta da RAN | vazão = base × razão(teto), com a curva medida no NORI (`cardl/calibration/slice_cap_curve_v5.json`, sha256 `d7c2f54e…`, 5 pontos com E2 real; satura em 40 % de PRB) |
| Máscara | Safety Guard da Fase 1 (`Refinement.check_bounds`): o Rogue é sempre mascarado |
| Recompensa | 0,6 × satisfação (0,6 crítica + 0,4 eMBB) + 0,3 × (1 − PRBs ativos) − 0,1 × mudanças de teto |
| Custo (CMDP) | 1 quando a fatia crítica recebe menos de 95 % da demanda; limite de 5 % das janelas |
| MAPPO | ator compartilhado (64×64), crítico centralizado com saídas de recompensa e de custo, PPO com clip 0,2, multiplicador de Lagrange por ascensão dual |
| Treino | sementes 101, 102 e 103; 2000 episódios cada (~15 min por semente, CPU) |
| Avaliação | 20 sementes separadas (9001–9020), política gulosa, contra B0–B3 no mesmo ambiente; B3 é o `Reasoning` real da Fase 1 |
| Proveniência | F2 `7e6da000`, F1 `a0cb21eb`, árvores limpas (`git_dirty: false`), sha256 de cada checkpoint no manifesto |

## 2. Resultados

| Política | Recompensa por episódio | Violação do SLA crítico | PRBs ativos | Satisfação crítica | Satisfação eMBB |
| :-- | :-: | :-: | :-: | :-: | :-: |
| B0 (última proposta) | 48,90 ± 0,44 | 0,949 | 10,0 % | 0,39 | 0,42 |
| B1 = B2 = B3 (H-RDL) | 67,05 ± 0,21 | 0,000 | 38,6 % | 1,00 | 1,00 |
| CA-RDL semente 101 | **68,19 ± 1,18** | 0,010 | 34,3 % | 1,00 | 0,80 |
| CA-RDL semente 102 | 66,17 ± 1,31 | 0,015 | 30,8 % | 1,00 | 0,68 |
| CA-RDL semente 103 | 62,72 ± 0,87 | **0,339** | 65,8 % | 0,92 | 1,00 |

Arquivos: `experiments/training/mappo_seed{101,102,103}/` (`evaluation.json`, `convergence.csv`, `training_manifest.json`, `actor_critic.pt`).

## 3. Leitura

1. **A H-RDL é quase ótima neste ambiente.** A proposta do RANSlicer já atende a demanda com margem pequena, e o TVS a escolhe sempre: nenhuma violação, mas também nenhuma economia.
2. **Duas de três sementes aprendem a trocar SLA por energia dentro do limite do CMDP.** Elas usam 11–20 % menos PRBs ativos e violam o SLA crítico em 1–1,5 % das janelas (limite: 5 %), à custa da fatia eMBB. A semente 101 supera a H-RDL na recompensa (68,19 contra 67,05).
3. **A terceira semente não converge** para uma política segura: 34 % de violações. Sem um critério de seleção de modelo, o MAPPO não é utilizável como está; a reserva para a H-RDL e a política A1 20002 são o que evita o risco.
4. **O treino não é determinístico na CPU.** A mesma semente produziu números diferentes numa rodada anterior, com o mesmo código e a árvore suja; essa rodada foi descartada. Para relato, fixar threads e algoritmos determinísticos do PyTorch.

**Estas medidas não são evidência de RAN** (`publication_eligible: false`): o ambiente é um substituto calibrado. A próxima etapa é uma validação pré-registrada na bancada NORI, com E2 real, comparando H-RDL e CA-RDL (semente selecionada por critério fixado antes) no S8.
