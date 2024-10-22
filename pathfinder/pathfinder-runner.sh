#!/bin/sh
export RPC_API_KEY=$(cat $RPC_API_KEY_FILE)
export GATEWAY_KEY=$(cat $GATEWAY_KEY_FILE)

echo "fuck youuuuuu " $RPC_API_KEY

./pathfinder                          \
	--data-directory /data/pathfinder \
	--storage.state-tries archive     \
	--network sepolia-testnet         \
	--http-rpc 0.0.0.0:9545           \
	--rpc.cors-domains "*"            \
	--rpc.root-version v07            \
	--ethereum.url $RPC_API_KEY       \
	--gateway-api-key $GATEWAY_KEY
