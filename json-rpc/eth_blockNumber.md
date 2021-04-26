# `eth_blockNumber`

| Spec | Description  |
| ----------- | --------------------------------------------------- |
| 1 |  Returns the number of the block that is the current chain head (the latest best processed and verified block on the chain) |
| 2 |  The number of the chain head is returned if the node has ability of serving the header, body, and the full state starting from the state root of the block having the number in a finite time  |
| 3 | The node may know a higher block number but still return a lower one if the lower number block has higher total difficulty or if the higher number block has not been fully processed yet |
| 4 | Provides no promise on for how long the node will keep the block details so if you request the block data for the given block number any time after receiving the block number itself, you may get a null response |
| 5 | Returns an error if the node has not yet processed or failed to process the genesis block. Some nodes MAY decide not to enable JSON RPC if the genesis block calculation has not been done yet |

# Tests

[...]

# Security Considerations
`eth_blockNumber` is considered safe

# Notes About Usage

### Description
`eth_blockNumber` is the most commonly called JSON RPC endpoint, yet it has some undefined edge cases. The goal is to assert its behavior for all current and future Ethereum 1.x client implementations.

### Parameters

_(none)_

### Returns

{[`Quantity`](./types/Quantity.md)} - number of the latest block

### Example

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

# Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
