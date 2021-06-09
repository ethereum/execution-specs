#!/bin/sh

# Translate BlockchainTests into t8n format.
#
# Note: t8n requires that hex values not have leading 0s, so you'll need to
# trim the manually (for now) :(.


if [ "$#" -ne 2 ]; then
    echo "Usage: debug.sh [test_path] [test_name]"
    exit
fi

jq --arg testname "${2}" '.[$testname] |
    .alloc = .pre | del(.pre) |
    .txs = .blocks[0].transactions |
    .env = .genesisBlockHeader |
    .env = {
        currentCoinbase:    .env.coinbase,
        currentDifficulty:  .env.difficulty,
        currentGasLimit:    .env.gasLimit,
        currentNumber:      .env.number,
        currentTimestamp:   .env.timestamp
    } |
    {alloc: .alloc, env: .env, txs: .txs }' ${1}

# evm t8n --input.alloc=stdin --input.env=stdin --input.txs=stdin --output.result=stdout --output.alloc=stdout

