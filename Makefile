# ============================================================================ #
#                         STARKNET NODE BENCHMAR RUNNER                        #
# ============================================================================ #

NODES    := madara
IMGS     := $(addsuffix /image.tar.gz,$(NODES))
VOLUMES  := $(addsuffix _runner_db,$(NODES))
SECRETS  := secrets/rpc_api.secret secrets/gateway_key.secret

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

.PHONY: start
start: images $(SECRETS)
	@for node in $(NODES); do \
		echo -e "$(TERTIARY)running$(RESET) $(PASS)$$node$(RESET)"; \
		docker-compose -f $$node/compose.yaml up -d; \
	done
	@echo -e "$(PASS)all services set up$(RESET)"

.PHONY: stop
stop:
	@for node in $(NODES); do \
		echo -e "$(TERTIARY)stopping $(WARN)$$node$(RESET)"; \
		docker-compose -f $$node/compose.yaml stop; \
	done
	@echo -e "$(WARN)all services stopped$(RESET)"

.PHONY: logs-madara
logs-madara:
	@echo -e "$(TERTIARY)logs for $(INFO)madara$(RESET)";
	@docker-compose -f madara/compose.yaml logs -f;

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

%image.tar.gz: node = $(@D)
%image.tar.gz: %default.nix
	@echo -e "$(TERTIARY)building$(RESET) $(PASS)$(node)$(RESET)"
	@docker image rm -f $(node):latest || true
	@docker build -t $(node):latest $(node)

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
