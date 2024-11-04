#!/bin/sh
export RPC_API_KEY=$(cat $RPC_API_KEY_FILE)

./pathfinder                                             \
	--data-directory /data/pathfinder                    \
	--storage.state-tries archive                        \
	--network custom                                     \
	--chain-id SN_SEPOLIA                                \
	--http-rpc 0.0.0.0:9545                              \
	--rpc.cors-domains "*"                               \
	--rpc.root-version v07                               \
	--feeder-gateway-url http://fgw:8080/feeder_gateway/ \
	--gateway-url http://fgw:8080/gateway/               \
	--ethereum.url $RPC_API_KEY
