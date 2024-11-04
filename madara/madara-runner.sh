#!/bin/sh
export RPC_API_KEY=$(cat $RPC_API_KEY_FILE)

./madara                                          \
	--name madara                                 \
	--base-path /data/madara                      \
	--network sepolia                             \
	--rpc-external                                \
	--rpc-cors all                                \
	--full                                        \
	--gateway-url http://fgw:8080/feeder_gateway/ \
	--l1-endpoint $RPC_API_KEY
