#!/bin/sh


cat $1 |
    jq ".${2}" |
    jq '.alloc = .pre | del(.pre)' |
    jq '.txs = .blocks[0].transactions' |
    jq '.env = .genesisBlockHeader' |
    jq '.env = {
        currentCoinbase:    .env.coinbase,
        currentDifficulty:  .env.difficulty,
        currentGasLimit:    .env.gasLimit,
        currentNumber:      .env.number,
        currentTimestamp:   .env.timestamp
    }' |
    jq '{alloc: .alloc, env: .env, txs: .txs }'
    # evm t8n --input.alloc=stdin --input.env=stdin --input.txs=stdin --output.result=stdout --output.alloc=stdout

