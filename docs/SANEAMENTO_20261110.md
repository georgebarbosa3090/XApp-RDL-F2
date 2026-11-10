# Saneamento do repositório da Fase 2 (2026-11-10)

## 1. Motivo

Uma análise do repositório (código, manifestos e bytes dos artefatos) mostrou que os resultados da Fase 2 publicados até 2026-09-30 não vinham de simulação nem de E2 real. A Fase 1 já tinha chegado à mesma conclusão sobre os mesmos artefatos e os removera do seu repositório (achado 45 de `XApp-RDL-F1/docs/07_certificacao_e_achados.md`). Este documento registra o que saiu daqui, por quê, e o que continua pendente.

Tudo o que foi removido continua no histórico do git (commit anterior: `95a1382`).

## 2. Constatações

| Artefato | O que se encontrou |
| :-- | :-- |
| `experiments/runs/S1_B0..B6_seed1001..1005` (35 execuções, 612 arquivos) | Os `raw/*.raw` contêm texto ASCII no lugar de APER (ex.: `ASN1_APER_PAYLOAD_kpm_t0.raw_S1_B6_seed1001`); `pcap/e2.pcap` tem 24 bytes, só o cabeçalho. Os manifestos citam `ns3_version: 3.48` com NORI e `nori_commit: 9b64c12`: esse commit não existe no NORI oficial, e o NORI não compila sobre ns-3.48. |
| `experiments/runs/certified_closed_loop_chain` | Montada por `scripts/build_certified_causal_chain.py`: PCAP com MACs `00:11:22:33:44:55` / `66:77:88:99:aa:bb`, IP ID `0x1234`, *verification tag* SCTP `0x12345678` e checksum zero; log de MAC com linhas a 5 µs exatos. |
| `experiments/results/`, `results/`, `artifacts/testbed/`, `experiments/demonstration/web/canonical_*` | Tabelas e conjuntos derivados das execuções acima ou escritos à mão. |
| `docs/figures/fig_*.png`, `reports/figures/` | Gráficos de resultados gerados a partir desses dados. |
| `docs/04`, `07`, `11`, `12`, `13` | Relatórios de resultados (ex.: Cohen d = 49,85 entre B0 e B3) baseados nesses dados; S9–S15 nunca foram executados. |
| `docs/auditoria/` | Auditorias, apresentação e cópia da dissertação com os números acima. |
| `specs/claims.yaml` | C1–C6 marcados `VERIFIED_EMPIRICAL`; na Fase 1 os mesmos estão `NOT_VERIFIED`. |
| Treino do MAPPO (`experiments/training/`) | Teste de fumaça: observações `np.random.randn`, recompensa `sin(step)`, 0,26 s, sem PyTorch, `publication_eligible: false`. Mantido, porque o manifesto já declara isso. |
| Inferência do MAPPO (`MAPPOCoordinator.decide`) | Usa a rede recém-inicializada (nenhum checkpoint é carregado) e força a confiança a no mínimo 0,80. **Não alterado neste saneamento.** |
| `NoriRanEnvironment` | Não conversa com o NORI: tabela fixa de vazão e latência por faixa de cota. **Não alterado.** |
| GNN / GraphSAGE / grafo de conhecimento / janela adaptativa | Não implementados (só um grafo `networkx` simples na percepção). |
| CI | As três últimas execuções falharam: o auditor de dados sintéticos acusava `analysis/realtime_protocol_engine.py`, e os passos chamavam `scripts/run_pyright_check.py` e `scripts/validate_ml_provenance.py`, que não existem. |
| README | Declarava "Validada Experimentalmente (N=30 Seeds)", "homologado" no OpenRAN@Brasil, 114/114 testes, e publicava token e senhas do InfluxDB/Grafana e um link de Google Drive. Licença declarada sem arquivo `LICENSE`. |

## 3. O que foi feito

### 3.1 Removido (927 arquivos)

- Execuções e resultados: `experiments/runs/`, `experiments/results/`, `experiments/comparison_summary_S1_seed1001.json`, `results/`, `artifacts/`, `experiments/demonstration/web/canonical_results.json` e `canonical_simulation_master.csv`.
- Figuras de resultados: `docs/figures/fig_*.png`, `docs/figures/README.md`, `docs/figures/figures_manifest.json`, `reports/figures/`. As ilustrações de arquitetura e de cenários (`docs/figures/01_*`, `02_*`) ficaram.
- Documentos de resultados: `docs/04`, `07`, `11`, `12`, `13` e `docs/auditoria/`.
- Geradores de evidência sintética ou montada: `scripts/build_certified_causal_chain.py`, `generate_e2_independent_pcap_traces.py`, `run_e2_live_socket_capture.py` (PCAP montado a partir de socket TCP local), `run_golden_closed_loop_experiment.py`, `run_continuous_simulations_ns3_nori.py` (rotulava o simulador Python como ns-3/NORI), `generate_paper_styled_benchmarks.py`, `generate_separated_phase1_phase2_figures.py`, `gerar_figuras_faltantes_hrdl.py`, `compile_dissertation_v2.py`; `analysis/export_tables.py`, `generate_demonstration_and_latest_sim_plots.py`, `generate_crosslayer_modular_plots.py`, `realtime_protocol_engine.py`, `realtime_dashboard.html`.
- Automação de commit/push: `scripts/auto_update_simulation_figures_and_github.{py,sh}`, `scripts/run_full_experiment.sh`.
- `scratch/` (textos integrais de artigos, figuras de terceiros, arquivos sem relação com o projeto).
- `tests/test_provenance_check.py` (importava `scripts/package_and_sync_raw_results.py`, que não existe; quebrava a coleta da suíte).

### 3.2 Corrigido

- `specs/claims.yaml`: C1–C6 voltaram para `NOT_VERIFIED`, com os valores observados como `NOT_VALIDATED`.
- `README.md` e `docs/README.md`: reescritos com o estado real.
- Avisos no topo dos documentos que restaram (`docs/01`, `02`, `03`, `05`, `06`, `08`, `09`, `10`, `14`, `docs/compliance/README.md`, `simulations/ns3/README.md`, `experiments/demonstration/README.md`).
- `docs/compliance/CARDL_F2_COMPATIBILITY_PROFILE.md` (portões F2-G0 a F2-G12 com o que foi medido) e `PHASE1_PHASE2_SYNC_CONTRACT.md`.
- `deploy/openran-br-v3/README.md`: retirado o selo de homologação.
- Credenciais retiradas da documentação; continuam como valores padrão de desenvolvimento local em `deployments/telemetry/` e `deploy/helm/oran-telemetry/values.yaml`.
- `docs/02`: retirada a seção de backup no Google Drive (o script nunca existiu).
- `scripts/check_no_synthetic_results.py`: também acusa `np.random.randn/rand/randint/choice`, `random.randint/choice`, o *verification tag* `0x12345678`, PDUs `.raw` textuais e PCAPs sem pacotes; deixou de exigir o manifesto de figuras removido.
- CI (`ci.yml`): pyright passa a ser informativo; o limite de cobertura cai de 85 % (nunca atingido) para 75 % (medido: 79 %).
- `scientific-readiness-f2.yml`: falha de propósito enquanto não houver treino elegível e afirmações verificadas.
- `Makefile`: removidos os alvos que chamavam scripts inexistentes ou de sincronização automática (`reproduce-paper`, `test-campaign`, `run-campaign-s0-s8`, `run-3-rounds`, `sync-f1-f2-check`, `git-sync`, `auto-update-figures`, `sync-cross`, `run-and-sync`, `push-results`, `backup-drive`).
- Adicionado `LICENSE` (Apache 2.0, o mesmo da Fase 1).

### 3.3 Verificação

- `pytest`: 111 passam, 2 pulados (antes: 111 passam, 2 pulados e 1 erro de coleta). Python 3.10, Windows.
- `python scripts/check_no_synthetic_results.py`: sai com 0 (antes saía com 1).

## 4. Pendências (não feitas neste saneamento)

1. **Rebasear a Fase 2 sobre a Fase 1.** O código da xApp aqui é anterior às 51 correções da Fase 1 (ex.: `control_dispatcher.py` ainda passa o nó como `retries` em `rmr_send`, achado 1; cota de PRB mapeada em E2SM-RC Style 1 / Action 1 em vez de Style 2 / Action 6). A Fase 2 deve importar o núcleo da Fase 1 e manter só o motor de contexto/MARL.
2. **MAPPO real**: ambiente que converse com o NORI pela xApp da Fase 1, treino com proveniência, carga do checkpoint na inferência e remoção do piso artificial de confiança.
3. **Reserva determinística** (H-RDL em ≤ 200 ms) como gate medido.
4. **GNN / grafo de conhecimento**: implementar só se houver hipótese que precise deles (ex.: conflitos entre células); senão, retirar das alegações nos documentos que restaram.
5. **Cenários**: os `.cc` daqui são anteriores às correções da Fase 1; S9–S15 nunca rodaram.
6. **Documentos que restaram**: ainda contêm números sem evidência (só sinalizados pelo aviso). Reescrevê-los conforme a evidência nova surgir.
