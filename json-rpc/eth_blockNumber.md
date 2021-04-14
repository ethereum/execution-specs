---
title: JSPON RPC eth_blockNumber Spec
author: Alita Moore (@alita-moore)
discussions-to: https://github.com/ethereum-oasis/eth1.x-JSON-RPC-API-standard
created: 2021-03-17
---

## Simple Summary
This document specifies in detail the expected behaviour of the eth_blockNumber; Eth 1.x JSON RPC endpoint.

## Abstract
`eth_blockNumber` and its sync modes are described here.

## Motivation
`eth_blockNumber` is the most commonly called JSON RPC endpoint, yet it has some undefined edge cases. The goal is to assert its behavior through all Ethereum 1.x client implementations.

## Specification

| Spec | Description  |
| ----------- | --------------------------------------------------- |
| **δ1** |  Returns the number of the block that is the current chain head (the latest best processed and verified block on the chain). |
| **δ2** |  The number of the chain head is returned if the node has ability of serving the header, body, and the full state starting from the state root of the block having the number in a finite time.  |
| **δ3** | The node may know a higher block number but still return a lower one if the lower number block has higher total difficulty or if the higher number block has not been fully processed yet. |
| **δ4** | Provides no promise on for how long the node will keep the block details so if you request the block data for the given block number any time after receiving the block number itself, you may get a null response. |
| **δ5** | Returns an error if the node has not yet processed or failed to process the genesis block. Some nodes MAY decide not to enable JSON RPC if the genesis block calculation has not been done yet. |

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
