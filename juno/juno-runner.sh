#!/bin/sh
export RPC_API_KEY=$(cat $RPC_API_KEY_FILE)

./juno                                                                    \
    --db-path /data/juno                                                  \
    --http                                                                \
    --http-port 6060                                                      \
    --http-host 0.0.0.0                                                   \
    --db-cache-size 3000                                                  \
    --cn-name "sepolia"                                                   \
    --cn-feeder-url http://fgw:8080/feeder_gateway/                       \
    --cn-gateway-url http://fgw:8080/gateway/                             \
    --cn-l1-chain-id 11155111                                             \
    --cn-l2-chain-id SN_SEPOLIA                                           \
    --cn-core-contract-address 0xe2bb56ee936fd6433dc0f6e7e3b8365c906aa057 \
    --cn-unverifiable-range "0,0"                                         \
    --eth-node $RPC_API_KEY
