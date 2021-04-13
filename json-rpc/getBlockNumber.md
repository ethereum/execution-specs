# eth_getBlockNumber

Returns the number of most recent block

## Parameters

None

# Development Section / Notes 

## Implemntations

### Geth 
As of `04/13/2021`
```go
// GetBlockNumber retrieves the block number belonging to the given hash
// from the cache or database
func (hc *HeaderChain) GetBlockNumber(hash common.Hash) *uint64 {
  if cached, ok := hc.numberCache.Get(hash); ok {
    number := cached.(uint64)
    return &number
  }
  number := rawdb.ReadHeaderNumber(hc.chainDb, hash)
  if number != nil {
    hc.numberCache.Add(hash, *number)
  }
  return number
}
```

### Nethermind 
As of `04/13/2021`
```cs
public Task<RpcResult<long?>> eth_blockNumber()
    => _proxy.SendAsync<long?>(nameof(eth_blockNumber));
```

### Besu
As of `04/13/2021`
``` java
public EthBlockNumber(final BlockchainQueries blockchain) {
  this(Suppliers.ofInstance(blockchain), false);
}
```

### Turbo Geth 
As of `04/13/2021`
```go
// BlockNumber implements eth_blockNumber. Returns the block number of most recent block.
func (api *APIImpl) BlockNumber(ctx context.Context) (hexutil.Uint64, error) {
	tx, err := api.db.BeginRo(ctx)
	if err != nil {
		return 0, err
	}
	defer tx.Rollback()
	execution, err := stages.GetStageProgress(tx, stages.Finish)
	if err != nil {
		return 0, err
	}
	return hexutil.Uint64(execution), nil
}
```

### OpenEthereum
As of `04/13/2021`
```rust
fn block_number(&self) -> Result<U256> {
    Ok(U256::from(self.client.chain_info().best_block_number))
}
```





