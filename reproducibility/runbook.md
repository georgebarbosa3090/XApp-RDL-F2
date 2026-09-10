# Runbook de Execução e Reprodutibilidade Experimental — Fase 2 (CA-RDL)

<div align="center">

**Protocolo de Reprodutibilidade MARL (MAPPO), Cenários 5G-A/6G e Validação de Governança O-RAN**  
*Autor: George Alexandro F. Barbosa — PPGC / Universidade Federal do Pará (UFPA)*

</div>

---

## 1. Pré-Requisitos do Sistema

* **Sistema Operacional:** Linux Ubuntu 22.04 LTS (WSL2 no Windows 11 ou Bare-Metal);
* **Contêineres e Cluster:** Docker Engine 24.0+ e k3d v5.6.0+;
* **Ambiente Python:** Python 3.10+ / 3.12 com dependências PyTorch, Gymnasium e PyCrate (`pip install -r requirements.txt`);
* **Toolchain de Compilação:** CMake 3.25+, Ninja e g++ 11+;
* **Simulador de Rádio 5G/6G:** Árvore de fontes do `ns-3.48` integrada com `5G-LENA v5.1` e `NORI`.

---

## 2. Roteiro Passo a Passo de Execução

### Passo 1: Inicialização do Cluster k3d (Escolha sua topologia)
```bash
# Opção 1: Single-Node (~450 MB RAM)
k3d cluster create rdl-cluster --servers 1 -p "36422:36422/sctp@server:0" -p "8080-8087:8080-8087@server:0" -p "4560-4561:4560-4561@server:0"

# Opção 2: Dual-Node (~900 MB RAM)
k3d cluster create rdl-cluster --servers 1 --agents 1 -p "36422:36422/sctp@server:0" -p "8080-8087:8080-8087@server:0" -p "4560-4561:4560-4561@server:0"

# Opção 3: Multi-Node (~1.5 GB RAM)
k3d cluster create rdl-cluster --servers 1 --agents 2 -p "36422:36422/sctp@server:0" -p "8080-8087:8080-8087@server:0" -p "4560-4561:4560-4561@server:0"
```

### Passo 2: Implantação da Infraestrutura Near-RT RIC e xApps Cognitivas
```bash
# Deploy via manifestos Kubernetes puros (Perfil OpenRAN@Brasil Blueprint v3)
kubectl apply -f deploy/openran-br-v3/config-map.yaml
kubectl apply -f deploy/openran-br-v3/service.yaml
kubectl apply -f deploy/openran-br-v3/deployment.yaml

# Verificar prontidão dos pods
kubectl get pods -n ricxapp -l app=iqos-xapp-rdl
```

### Passo 3: Execução da Suíte de 3 Simulações Consecutivas (MARL, 5G-A MIMO & 6G ISAC)
```bash
# Executa os cenários TVS/EEVS (MAPPO), Massive MIMO/ISAC e Cross-Tier (N = 30 Runs)
python scripts/run_3_consecutive_simulations.py
```

### Passo 4: Execução dos Testes Automatizados e Interoperabilidade
```bash
pytest tests/ -v
```

### Passo 5: Geração de Figuras Científicas e Radar Holístico (300 DPI)
```bash
python scripts/generate_sbrc_figures.py
```
