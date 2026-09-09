.PHONY: build build-no-cache test validate package onboard install status status-f2 logs logs-f2 smoke-test uninstall helm-deploy helm-deploy-f2 helm-upgrade-f2 helm-uninstall-f2 helm-test-f2 test-f2 test-3xapps cluster-create cluster-delete cluster-recreate sync-ns3-scratch setup-ns3 run-scenario1 run-scenario1-baseline run-scenario2 run-scenario2-baseline run-scenario3 run-scenario4 run-scenario5 run-all-scenarios run-baseline run-rdl run-experiments run-suite analyze-benchmarks view-results push-results sync auto-sync rollback rollback-push rollback-clean rollback-list

NS3_DIR ?= $(HOME)/ns3-oran-workspace/ns-3-oran

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 2.0.0
CHART_DIR ?= deploy/helm/iqos-xapp-rdl
NAMESPACE_RIC ?= ricplt
NAMESPACE ?= ricxapp
RELEASE_NAME_F2 ?= ricxapp-iqos-xapp-rdl-f2
CLUSTER_NAME ?= rancher-lab

# -------------------------------------------------------------
# Build e Testes Locais da xApp RDL Fase 2
# -------------------------------------------------------------
build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

# -------------------------------------------------------------
# Deploy Helm Exclusivo para RDL Fase 2 (CA-RDL / MARL)
# Premissa: Near-RT RIC e as 3 Reference xApps ja estao rodando!
# -------------------------------------------------------------
helm-deploy: helm-deploy-f2

helm-deploy-f2:
	@echo "Implantando/Atualizando exclusivamente a xApp RDL Fase 2 ($(RELEASE_NAME_F2))..."
	bash scripts/deploy_rdl_phase2.sh

helm-upgrade-f2:
	@echo "Executando Helm Upgrade da release $(RELEASE_NAME_F2)..."
	helm upgrade --install $(RELEASE_NAME_F2) $(CHART_DIR) \
	  --namespace $(NAMESPACE) \
	  --set image.repository=$(IMAGE_NAME) \
	  --set image.tag=$(IMAGE_TAG) \
	  --set image.pullPolicy=Never \
	  --set fullnameOverride=$(RELEASE_NAME_F2) \
	  --set env.useFakeSdl="false" \
	  --set env.rmrWaitForReady="false" \
	  --set env.enableTorch="true"

helm-uninstall-f2:
	@echo "Removendo exclusivamente a xApp RDL Fase 2 ($(RELEASE_NAME_F2))..."
	helm uninstall $(RELEASE_NAME_F2) -n $(NAMESPACE) || echo "Release $(RELEASE_NAME_F2) nao encontrada."

status-f2:
	@echo "=== Status das xApps no Namespace $(NAMESPACE) ==="
	@kubectl get pods -n $(NAMESPACE) -o wide
	@echo ""
	@echo "=== Pod da xApp RDL Fase 2 ==="
	@kubectl get pods -n $(NAMESPACE) -l app=$(RELEASE_NAME_F2) -o wide

logs-f2:
	kubectl logs -l app=$(RELEASE_NAME_F2) -n $(NAMESPACE) -f

test-f2:
	@echo "Testando endpoints da xApp RDL Fase 2 (CA-RDL / MARL)..."
	@curl -i http://localhost:8080/health || true
	@echo ""
	@echo "Métricas Prometheus:"
	@curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_" || true

test-3xapps:
	@echo "Testando integridade das 3 Reference xApps no cluster..."
	bash scripts/verify_3_xapps.sh

# -------------------------------------------------------------
# Gestão do Cluster k3d (Topologias: 1 Nó, 2 Nós, 3 Nós)
# -------------------------------------------------------------
cluster-create: cluster-create-1node

cluster-create-1node:
	@echo "Criando cluster k3d $(CLUSTER_NAME) [Topologia: 1 Nó Único (Control-Plane + Worker)]..."
	k3d cluster create $(CLUSTER_NAME) --servers 1 --agents 0 \
	  --port "36422:36422/SCTP@server:0" \
	  --port "8080:8080@server:0" \
	  --port "8081:8081@server:0" \
	  --port "4560:4560@server:0" \
	  --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config
	@kubectl label namespace ricxapp istio-injection=enabled --overwrite 2>/dev/null || true
	@kubectl label namespace ricplt istio-injection=enabled --overwrite 2>/dev/null || true

cluster-create-2nodes:
	@echo "Criando cluster k3d $(CLUSTER_NAME) [Topologia: 2 Nós (1 Server + 1 Agent)]..."
	k3d cluster create $(CLUSTER_NAME) --servers 1 --agents 1 \
	  --port "36422:36422/SCTP@server:0" \
	  --port "8080:8080@server:0" \
	  --port "8081:8081@server:0" \
	  --port "4560:4560@server:0" \
	  --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config

cluster-create-3nodes:
	@echo "Criando cluster k3d $(CLUSTER_NAME) [Topologia: 3 Nós (1 Server + 2 Agents)]..."
	k3d cluster create $(CLUSTER_NAME) --servers 1 --agents 2 \
	  --port "36422:36422/SCTP@server:0" \
	  --port "8080:8080@server:0" \
	  --port "8081:8081@server:0" \
	  --port "4560:4560@server:0" \
	  --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config

cluster-delete:
	k3d cluster delete $(CLUSTER_NAME)

cluster-recreate: cluster-delete cluster-create-1node

clean-all:
	@bash scripts/cleanup_all.sh

PYTHON ?= python3

# -------------------------------------------------------------
# Simulações ns-3 e Pipelines Experimentais
# -------------------------------------------------------------
sync-ns3-scratch:
	@echo "Sincronizando cenários C++ com o diretório scratch do ns-3 ($(NS3_DIR)/scratch)..."
	@mkdir -p $(NS3_DIR)/scratch
	@cp -f simulations/ns3/*.cc $(NS3_DIR)/scratch/

setup-ns3:
	bash scripts/setup_ns3.sh

run-scenario1: sync-ns3-scratch
	@echo "Executando Cenário 1: Energy Saving vs QoS (EEVS) com E2 ativo..."
	cd $(NS3_DIR) && export NS_LOG="ScenarioRdlEnergyVsQos=level_all" && ./ns3 run "scratch/scenario_rdl_energy_vs_qos --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"
	@echo "\n[+] Atualizando relatórios locais e sincronizando com o GitHub..."
	@$(PYTHON) scripts/run_experiment_suite.py

run-scenario1-baseline: sync-ns3-scratch
	@echo "Executando Cenário 1: Energy Saving vs QoS (Baseline / Standalone)..."
	cd $(NS3_DIR) && ./ns3 run "scratch/scenario_rdl_energy_vs_qos --enableE2=false --simTime=30"
	@echo "\n[+] Atualizando relatórios locais e sincronizando com o GitHub..."
	@$(PYTHON) scripts/run_experiment_suite.py

run-scenario2: sync-ns3-scratch
	@echo "Executando Cenário 2: Traffic Steering vs Slicing (TVS) com E2 ativo..."
	cd $(NS3_DIR) && export NS_LOG="ScenarioRdlTvsConflict=level_all" && ./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"
	@echo "\n[+] Atualizando relatórios locais e sincronizando com o GitHub..."
	@$(PYTHON) scripts/run_experiment_suite.py

run-scenario2-baseline: sync-ns3-scratch
	@echo "Executando Cenário 2: Traffic Steering vs Slicing (Baseline / Standalone)..."
	cd $(NS3_DIR) && ./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=false --simTime=30"
	@echo "\n[+] Atualizando relatórios locais e sincronizando com o GitHub..."
	@$(PYTHON) scripts/run_experiment_suite.py

run-scenario3: sync-ns3-scratch
	@echo "Executando Cenário 3: 5G-Advanced Multi-Carrier (FR1/FR3) & Massive MIMO UPA..."
	cd $(NS3_DIR) && export NS_LOG="ScenarioRdl5gaMulticarrierMimo=level_all" && ./ns3 run "scratch/scenario_rdl_5ga_multicarrier_mimo --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=40"
	@echo "\n[+] Atualizando relatórios locais e sincronizando com o GitHub..."
	@$(PYTHON) scripts/run_experiment_suite.py

run-scenario4: sync-ns3-scratch
	@echo "Executando Cenário 4: 6G ISAC (Sensoriamento Radar vs Comunicação 28 GHz)..."
	cd $(NS3_DIR) && export NS_LOG="ScenarioRdl6gIsacSensingCoexistence=level_all" && ./ns3 run "scratch/scenario_rdl_6g_isac_sensing_coexistence --sensingRatio=0.35 --simTime=30"
	@echo "\n[+] Atualizando relatórios locais e sincronizando com o GitHub..."
	@$(PYTHON) scripts/run_experiment_suite.py

run-scenario5: sync-ns3-scratch
	@echo "Executando Cenário 5: 6G Governança Cross-Tier & Escudo Anti-Rogue xApp..."
	cd $(NS3_DIR) && export NS_LOG="ScenarioRdl6gCrossTierGovernance=level_all" && ./ns3 run "scratch/scenario_rdl_6g_cross_tier_governance --lockout=true --simTime=35"
	@echo "\n[+] Atualizando relatórios locais e sincronizando com o GitHub..."
	@$(PYTHON) scripts/run_experiment_suite.py

run-all-scenarios: sync-ns3-scratch
	bash scripts/run_all_scenarios_suite.sh

run-baseline: sync-ns3-scratch
	bash scripts/run_baseline_experiment.sh

run-rdl: sync-ns3-scratch
	bash scripts/run_rdl_experiment.sh

run-experiments: sync-ns3-scratch
	bash scripts/run_full_experiment.sh

run-suite:
	@$(PYTHON) scripts/run_experiment_suite.py

analyze-benchmarks:
	@$(PYTHON) scripts/run_experiment_suite.py

view-results:
	@cat experiments/results/relatorio_comparativo.md

push-results:
	@echo "Sincronizando resultados com o GitHub..."
	git add experiments/results/ docs/ scripts/
	git commit -m "chore(experiments): upload latest ns-3 MARL benchmark results [skip ci]" || echo "Nenhum dado novo."
	git push origin main || echo "Aviso no push."

sync:
	@bash scripts/git_sync.sh "$(MSG)"

auto-sync:
	@bash scripts/git_auto_sync.sh $(INTERVAL)

