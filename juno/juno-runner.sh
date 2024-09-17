#!/bin/sh
export RPC_API_KEY=$(cat $RPC_API_KEY_FILE)
export GATEWAY_KEY=$(cat $GATEWAY_KEY_FILE)

./juno                        \
    --db-path /data/juno      \
    --network sepolia         \
    --http-port 6060          \
    --http-host 0.0.0.0       \
    --db-cache-size 3000      \
    --eth-node $RPC_API_KEY   \
    --gw-api-key $GATEWAY_KEY
