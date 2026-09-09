# Armazenamento de Dados Brutos de Co-Simulacao (Raw Traces)

Devido ao volume de dados gerado pelo `FlowMonitor` do ns-3 e pelos traces PCAP/SCTP de cada rodada estocastica ($N = 30$ sementes por cenario), os arquivos brutos estao hospedados no **Google Drive oficial do projeto**, enquanto o **GitHub armazena os datasets limpos e processados (`experiments/results/data/*.csv`)**.

### [Acessar Pasta de Dados Brutos no Google Drive](https://drive.google.com/drive/folders/1dC5g5iAVqGcdiXKQPyyUxES1rNjdZw8x)

#### Pacotes de Dados Brutos e Hashes SHA-256:

| Cenario | Arquivo Compactado | Arquivos | Tamanho | Checksum SHA-256 |
| :--- | :--- | :---: | :---: | :--- |
| **baseline** | `raw_traces_baseline_seeds_1001_1030.zip` | `30` | `0.01 MB` | `498b82bc452ae2f23f229045c9d1c38399a7e6c633e0d5ea41abaae5a77e5397` |
| **rdl_phase1** | `raw_traces_rdl_phase1_seeds_1001_1030.zip` | `30` | `0.01 MB` | `a6e1d4fbc83fa9cbcd5e78b0bcbf7a87f63da673e87deb286a80a3e49adde6f9` |
| **rdl_phase2** | `raw_traces_rdl_phase2_seeds_1001_1030.zip` | `30` | `0.01 MB` | `0111df2de459696cfb139d16b34122b372faf9d9bf88ea2e21e7d0e3a7f394fa` |

---
### Como empacotar traces de novos ensaios:
```bash
# Modo demonstracao com sementes 1001-1030
python scripts/package_and_sync_raw_results.py --mode demo

# Modo estrito de experimentacao (valida cadeia de custodia completa)
python scripts/package_and_sync_raw_results.py --mode experiment --strict
```
