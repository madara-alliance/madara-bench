#!/bin/sh
export RPC_API_KEY=$(cat $RPC_API_KEY_FILE)
export GATEWAY_KEY=$(cat $GATEWAY_KEY_FILE)

./madara                        \
	--name madara               \
	--base-path /data/madara    \
	--network sepolia           \
	--full                      \
	--feeder-gateway-enable     \
	--gateway-enable            \
	--gateway-external          \
	--l1-endpoint $RPC_API_KEY  \
	--gateway-key $GATEWAY_KEY
