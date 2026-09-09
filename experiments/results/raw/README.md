# Armazenamento de Dados Brutos de Co-Simulacao (Raw Traces)

Devido ao volume de dados gerado pelo `FlowMonitor` do ns-3 e pelos traces PCAP/SCTP de cada rodada estocastica ($N = 30$ sementes por cenario), os arquivos brutos estao hospedados no **Google Drive oficial do projeto**, enquanto o **GitHub armazena os datasets limpos e processados (`experiments/results/data/*.csv`)**.

### [Acessar Pasta de Dados Brutos no Google Drive](https://drive.google.com/drive/folders/1dC5g5iAVqGcdiXKQPyyUxES1rNjdZw8x)

#### Pacotes de Dados Brutos e Hashes SHA-256:

| Cenario | Arquivo Compactado | Arquivos | Tamanho | Checksum SHA-256 |
| :--- | :--- | :---: | :---: | :--- |
| **baseline** | `raw_traces_baseline_seeds_1001_1030.zip` | `30` | `0.03 MB` | `b2b6551cc47bca5d740272086363600d2ce7de0cb594ffd5ea0b9e05965e0426` |
| **rdl_phase1** | `raw_traces_rdl_phase1_seeds_1001_1030.zip` | `30` | `0.02 MB` | `8eb8c5e771a39fe78000a9d7c03a9d067fa105d03ab0726569f7618c104c85fa` |
| **rdl_phase2** | `raw_traces_rdl_phase2_seeds_1001_1030.zip` | `30` | `0.02 MB` | `9955ce2f577a86ab40b1cf467352bfef50f4fccde0bf4961375f42260f09ddf1` |

---
### Como empacotar traces de novos ensaios:
```bash
# Modo demonstracao com sementes 1001-1030
python scripts/package_and_sync_raw_results.py --mode demo

# Modo estrito de experimentacao (valida cadeia de custodia completa)
python scripts/package_and_sync_raw_results.py --mode experiment --strict
```
