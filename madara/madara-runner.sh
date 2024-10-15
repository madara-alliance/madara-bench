#!/bin/sh
export RPC_API_KEY=$(cat $RPC_API_KEY_FILE)
export GATEWAY_KEY=$(cat $GATEWAY_KEY_FILE)

./madara                       \
	--name madara              \
	--base-path /data/madara   \
	--network sepolia          \
	--rpc-external             \
	--rpc-cors all             \
	--full                     \
	--l1-endpoint $RPC_API_KEY \
	--gateway-key $GATEWAY_KEY
