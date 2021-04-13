---
title: JSPON RPC eth_blockNumber Spec
author: Tomasz K. Stanczak (@tkstanczak)
discussions-to: https://github.com/ethereum-oasis/eth1.x-JSON-RPC-API-standard
created: 2021-04-13
---

## Simple Summary
This document specifies in detail the expected behaviour of the eth_blockNumber Eth 1.x JSON RPC endpoint.

## Abstract
We cover basic behaviour and edge cases for various sync modes.

## Motivation
eth_blockNumber is the most commonly called JSON RPC endpoint, yet it has some undefined edge cases that needs specification so that the behaviour is consistent in all situation on all Ethereum 1.x client implementations.

## Specification

### eth_blockNumber

### Description
- Returns the number of the block that is the current chain head (the latest best processed and verified block on the chain).
- The number of the chain head is returned if the node has ability of serving the header, body, and the full state starting from the state root of the block having the number in a finite time.
- The node may know a higher block number but still return a lower one if the lower number block has higher total difficulty or if the higher number block has not been fully processed yet.
- Provides no promise on for how long the node will keep the block details so if you request the block data for the given block number any time after receiving the block number itself, you may get a null response.
- Returns an error if the node has not yet processed or failed to process the genesis block. Some nodes MAY decide not to enable JSON RPC if the genesis block calculation has not been done yet.

## Spec

##### Parameters

_(none)_

##### Returns

{[`Quantity`](./types/Quantity.md)} - number of the latest block

##### Example

```sh
# Request
curl -X POST --data '{
    "id": 1337,
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": []
}' <url>

# Response
{
    "id": 1337,
    "jsonrpc": "2.0",
    "result": "0xc94"
}
```

## Rationale
The definition of being able to serve the full state has been introduced to clarify the behaviour in the midst of fast sync and similar.

## Test Cases
TBD

## Security Considerations
`eth_blockNumber` is considered to be safe

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
