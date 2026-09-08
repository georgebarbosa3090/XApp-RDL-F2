# Armazenamento de Dados Brutos de Co-Simulacao (Raw Traces)

Devido ao volume de dados gerado pelo `FlowMonitor` do ns-3 e pelos traces PCAP/SCTP de cada rodada estocastica ($N = 30$ sementes por cenario), os arquivos brutos estao hospedados no **Google Drive oficial do projeto**, enquanto o **GitHub armazena os datasets limpos e processados (`experiments/results/data/*.csv`)**.

### [Acessar Pasta de Dados Brutos no Google Drive](https://drive.google.com/drive/folders/1dC5g5iAVqGcdiXKQPyyUxES1rNjdZw8x)

#### Pacotes de Dados Brutos e Hashes SHA-256:

| Cenario | Arquivo Compactado | Tamanho | Checksum SHA-256 |
| :--- | :--- | :---: | :--- |
| **baseline** | `raw_traces_baseline_seeds_1001_1030.zip` | `0.01 MB` | `f3529f458b5f07903de8322bac2e63188401c3093e41b2616711db3b9c7bba07` |
| **rdl_phase1** | `raw_traces_rdl_phase1_seeds_1001_1030.zip` | `0.01 MB` | `7e2ae0e19eadcfc04ad563dd97f05e5601bb94365a210b84fa07b8c0949646bf` |
| **rdl_phase2** | `raw_traces_rdl_phase2_seeds_1001_1030.zip` | `0.01 MB` | `b243239f75cb3af96b4ac35abafc28defd9d18299a0e3a623895199b4a5cb3b2` |

---
### Como enviar / sincronizar novos traces:
```bash
python scripts/package_and_sync_raw_results.py
```
