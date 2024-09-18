# ============================================================================ #
#                         STARKNET NODE BENCHMAR RUNNER                        #
# ============================================================================ #

NODES    := madara juno pathfinder
IMGS     := $(addsuffix /image.tar.gz,$(NODES))
VOLUMES  := $(addsuffix _runner_db,$(NODES))
SECRETS  := secrets/rpc_api.secret     \
            secrets/rpc_api_ws.secret  \
			secrets/gateway_key.secret

# dim white italic
TERTIARY := \033[2;3;37m

# bold cyan
PASS     := \033[1;36m

# bold green
PASS     := \033[1;32m

# bold red
WARN     := \033[1;31m

RESET    := \033[0m

.PHONY: all
all: help

.PHONY: help
help:
	@echo "TODO(help)"

.PHONY: start-madara
start-madara: images $(SECRETS)
	@echo -e "$(TERTIARY)running$(RESET) $(PASS)madara$(RESET)"
	@docker-compose -f madara/compose.yaml up -d

.PHONY: start-juno
start-juno: images $(SECRETS)
	@echo -e "$(TERTIARY)running$(RESET) $(PASS)juno$(RESET)"
	@docker-compose -f juno/compose.yaml up -d

.PHONY: start-pathfinder
start-pathfinder: images $(SECRETS)
	@echo -e "$(TERTIARY)running$(RESET) $(PASS)pathfinder$(RESET)"
	@docker-compose -f pathfinder/compose.yaml up -d

.PHONY: start
start: start-madara start-juno start-pathfinder
	@echo -e "$(PASS)all services set up$(RESET)"

.PHONY: stop-madara
stop-madara:
	echo -e "$(TERTIARY)stopping $(WARN)madara$(RESET)"; \
	docker-compose -f madara/compose.yaml stop; \

.PHONY: stop-juno
stop-juno:
	echo -e "$(TERTIARY)stopping $(WARN)juno$(RESET)"; \
	docker-compose -f juno/compose.yaml stop; \

.PHONY: stop-pathfinder
stop-pathfinder:
	echo -e "$(TERTIARY)stopping $(WARN)pathfinder$(RESET)"; \
	docker-compose -f pathfinder/compose.yaml stop; \

.PHONY: stop
stop: stop-madara stop-juno stop-pathfinder
	@echo -e "$(WARN)all services stopped$(RESET)"

.PHONY: logs-madara
logs-madara:
	@echo -e "$(TERTIARY)logs for $(INFO)madara$(RESET)";
	@docker-compose -f madara/compose.yaml logs -f;

.PHONY: logs-juno
logs-juno:
	@echo -e "$(TERTIARY)logs for $(INFO)juno$(RESET)";
	@docker-compose -f juno/compose.yaml logs -f;

.PHONY: logs-pathfinder
logs-pathfinder:
	@echo -e "$(TERTIARY)logs for $(INFO)pathfinder$(RESET)";
	@docker-compose -f pathfinder/compose.yaml logs -f;

.PHONY: images
images: $(IMGS)

.PHONY: clean
clean: stop
	@echo -e "$(TERTIARY)pruning containers$(RESET)"
	@docker container prune -f
	@echo -e "$(TERTIARY)pruning images$(RESET)"
	@docker image prune -f
	@echo -e "$(WARN)images cleaned$(RESET)"

.PHONY: fclean
fclean: clean
	@echo -e "$(TERTIARY)removing local images tar.gz$(RESET)"
	@rm -rf $(IMGS)
	@echo -e "$(TERTIARY)removing local database volumes$(RESET)"
	@for volume in $(VOLUMES); do  \
		docker volume rm -f $$volume; \
	done
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

.PHONY: restart
restart: clean
	@make --silent start

.PHONY: frestart
frestart: fclean
	@make --silent start

.PHONY: debug
debug:
	@echo $(NODES)
	@echo $(IMGS)

.SECONDEXPANSION:
%image.tar.gz: node = $(@D)
%image.tar.gz: %Dockerfile %$$(node)-runner.sh
	@echo -e "$(TERTIARY)building$(RESET) $(PASS)$(node)$(RESET)"
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
