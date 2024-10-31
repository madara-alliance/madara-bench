# ============================================================================ #
#                         STARKNET NODE BENCHMAR RUNNER                        #
# ============================================================================ #

NODES    := madara juno pathfinder
IMGS     := $(addsuffix /image.tar.gz,$(NODES))
VOLUMES  := $(addsuffix _runner_db,$(NODES))
SECRETS  := secrets/rpc_api.secret     \
            secrets/rpc_api_ws.secret  \
            secrets/gateway_key.secret \
	    secrets/db_password.secret

DEPS     := poetry install
RUNNER   := poetry run fastapi run app

define HELP
Starknet Node Benchmark Runner

Starts mulitple starknet RPC nodes in individual, isolated and resource-
constrained containers for benchmarking. An endpoint will be exposed at
0.0.0.0:8000/docs where you can visually query RPC methods and run benchmarks
on each node. You can also query this endpoint more traditionally via JSON RPC
in cases where automation is necessary.

Usage:
  make <target>

Targets:

  [ RUNNING NODES ]

  Runs nodes, automatically building the required images if they have not 
  already been generated (this will take some time). Note that it is also 
  required for you to have added the necessary secrets to `./secrets/`, or the
  nodes will fail to start.

  - start-madara       Start the Madara node
  - start-juno         Start the Juno node
  - start-pathfinder   Start the Pathfinder node
  - start-db           Start postgresql local db at ./db/data
  - start-service      Start api service at 0.0.0.0:8000/docs
  - start              Start all nodes and api service

  [ STOPPING NODES ]

  Note that this will only pause container execution and not delete them, any 
  volume or image.

  - stop-madara        Stop the Madara node
  - stop-juno          Stop the Juno node
  - stop-pathfinder    Stop the Pathfinder node
  - stop-db            Stop postgresql local db at ./db/data
  - stop               Stop all nodes

  [ RESTARTING NODES ]

  Restarts nodes, possibly cleaning build artefacts, containers, images and
  volumes in the process. Note that it is also required for you to have added
  the necessary secrets to `./secrets/`, or the nodes will fail to restart.

  - restart-madara     Restart the Madara node
  - restart-juno       Restart the Juno node
  - restart-pathfinder Restart the Pathfinder node
  - restart            Restart all nodes
  - frestart           Perform full clean and restart all nodes

  [ LOGGING NODES ]

  This will show logging outputs for a node's container. Defaults to following
  the output, <Ctrl-C> to quit.

  - logs-madara        View logs for the Madara node
  - logs-juno          View logs for the Juno node
  - logs-pathfinder    View logs for the Pathfinder node

  [ BUILDING DEPENDENCIES ]

  Images are built using local dockerfiles running a version of each node 
  pinned to a specif release or commit. Note that to avoid continuousy 
  rebuilding images those are export to a `tar.gz` as build artefacts.

  - images             Build Docker images for all nodes

  [ CLEANING DEPENDECIES ]

  Will remove running containers, images and even volumes. Use the latter with
  care as reseting node volumes will force a resync from genesys.

  - clean              Stop containers and prune images
  - clean-db           Perform clean and remove local volumes and database
  - fclean             Perform clean-db and remove local images

  [ OTHER COMMANDS ]

  - help               Show this help message

endef
export HELP

# dim white italic
DIM := \033[2;3;37m

# bold cyan
INFO     := \033[1;36m

# bold green
PASS     := \033[1;32m

# bold red
WARN     := \033[1;31m

RESET    := \033[0m

.PHONY: all
all: help

.PHONY: help
help:
	@echo "$$HELP"

.PHONY: start-db
start-db:
	@echo -e "$(DIM)starting$(RESET) $(PASS)database$(RESET)"
	@docker compose -f db/compose.yaml up -d

.PHONY: start-madara
start-madara: images $(SECRETS)
	@echo -e "$(DIM)running$(RESET) $(PASS)madara$(RESET)"
	@docker-compose -f madara/compose.yaml up -d

.PHONY: start-juno
start-juno: images $(SECRETS)
	@echo -e "$(DIM)running$(RESET) $(PASS)juno$(RESET)"
	@docker-compose -f juno/compose.yaml up -d

.PHONY: start-pathfinder
start-pathfinder: images $(SECRETS)
	@echo -e "$(DIM)running$(RESET) $(PASS)pathfinder$(RESET)"
	@docker-compose -f pathfinder/compose.yaml up -d

.PHONY: start-service
start-service: start-db
	@$(DEPS)
	@$(RUNNER)

.PHONY: start
start: start-db
	@make --silent start-madara start-juno start-pathfinder
	@echo -e "$(PASS)all services are up$(RESET)"
	@$(DEPS)
	@$(RUNNER)

.PHONY: stop-db
stop-db:
	@echo -e "$(DIM)stopping$(RESET) $(WARN)database$(RESET)"
	@docker compose -f db/compose.yaml stop

.PHONY: stop-madara
stop-madara:
	@echo -e "$(DIM)stopping$(RESET) $(WARN)madara$(RESET)"
	@docker-compose -f madara/compose.yaml stop

.PHONY: stop-juno
stop-juno:
	@echo -e "$(DIM)stopping$(RESET) $(WARN)juno$(RESET)"
	@docker-compose -f juno/compose.yaml stop

.PHONY: stop-pathfinder
stop-pathfinder:
	@echo -e "$(DIM)stopping$(RESET) $(WARN)pathfinder$(RESET)"
	@docker-compose -f pathfinder/compose.yaml stop

.PHONY: stop
stop: stop-madara stop-juno stop-pathfinder
	@make --silent stop-db
	@echo -e "$(WARN)all services stopped$(RESET)"

.PHONY: logs-madara
logs-madara:
	@echo -e "$(DIM)logs for$(RESET) $(INFO)madara$(RESET)";
	@docker-compose -f madara/compose.yaml logs -f -n 100;

.PHONY: logs-juno
logs-juno:
	@echo -e "$(DIM)logs for$(RESET) $(INFO)juno$(RESET)";
	@docker-compose -f juno/compose.yaml logs -f -n 100;

.PHONY: logs-pathfinder
logs-pathfinder:
	@echo -e "$(DIM)logs for$(RESET) $(INFO)pathfinder$(RESET)";
	@docker-compose -f pathfinder/compose.yaml logs -f -n 100;

.PHONY: images
images: $(IMGS)

.PHONY: clean
clean: stop
	@echo -e "$(DIM)pruning containers$(RESET)"
	@docker container prune -f
	@echo -e "$(DIM)pruning images$(RESET)"
	@docker image prune -f
	@echo -e "$(WARN)images cleaned$(RESET)"

.PHONY: clean-db
clean-db:
	@echo -e "$(WARN)This action will result in irrecoverable loss of data!$(RESET)"
	@echo -e "$(DIM)Are you sure you want to proceed?$(RESET) $(PASS)[y/N] $(RESET)" && \
	read ans && \
	case "$$ans" in \
		[yY]*) true;; \
		*) false;; \
	esac
	@make --silent clean
	@echo -e "$(DIM)removing node database volumes$(RESET)"
	@for volume in $(VOLUMES); do  \
		docker volume rm -f $$volume; \
	done
	@echo -e "$(DIM)removing benchmark database$(RESET)"
	@sudo rm -rf ./db/data

.PHONY: fclean
fclean: clean-db
	@echo -e "$(DIM)removing local images tar.gz$(RESET)"
	@rm -rf $(IMGS)
	@echo -e "$(WARN)artefacts cleaned$(RESET)"

.PHONY: restart-madara
restart-madara: clean
	@make --silent start-madara

.PHONY: restart-juno
restart-juno: clean
	@make --silent start-juno

.PHONY: restart-pathfinder
restart-pathfinder: clean
	@make --silent start-pathfinder

.PHONY: restart-db
restart-db: clean
	@make --silent start-db

.PHONY: restart
restart: clean
	@make --silent start

.PHONY: frestart
frestart: fclean
	@make --silent start

.SECONDEXPANSION:
%image.tar.gz: node = $(@D)
%image.tar.gz: %Dockerfile %$$(node)-runner.sh
	@echo -e "$(DIM)building$(RESET) $(PASS)$(node)$(RESET)"
	@docker image rm -f $(node):latest || true
	@docker build -t $(node):latest $(node)
	@docker image save -o $(node)/image.tar.gz $(node):latest

#	Nix Image build has had to been remove following the introduction of scarb
#	into the build process. This is because scarb needs to download depencies
#	during the madara build process, which results in an impure derivation.
#	This does not play well with nix. The only solution to this would be to
#	propose an upstream pr to the scarb repo which allows scarb to re-use
#	locally available dependencies, even if they were not downloaded by it.
#
#	@nix-build $(node) -o $(node)/result
#	@$(node)/result/bin/copyto $(node)/image.tar.gz
#	@docker load -i $(node)/image.tar.gz
