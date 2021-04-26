

# `eth_call`
The key words “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in [RFC-2119](https://www.ietf.org/rfc/rfc2119.txt).

specification | description 
--|--
1         | `eth_call` MUST NOT affect on-chain state|
2         | `eth_call` MUST NOT accept requests that are not in valid JSON format
3         | `eth_call` MUST return a response in valid JSON format
4         | `eth_call` MUST accept a `params` parameter [JSON Array](https://tools.ietf.org/html/rfc7159#section-5) of length 2, and its first item containing a [JSON Object](https://tools.ietf.org/html/rfc7159#section-4) with keys known here as the `input parameters`
4.1       | `eth_call` MUST accept an input parameter `from` of type `DATA` [!]
4.1.1     | `eth_call` MUST accept requests with the from input parameter undefined
4.1.1.1   | `eth_call` MUST consider CALLER account to be `0x0000000000000000000000000000000000000000000000000000000000000000` if `from` is not defined
4.1.2     | `eth_call` MUST accept requests with the `from` input parameter defined
4.1.2.1   | `eth_call` MUST only accept requests with the `from` parameter defined as a hex string with length 40
4.1.2.1.1 | `eth_call` SHOULD throw error `-32602` [!] on improper length with message as `invalid argument 0: hex string has length {length}, want 40 for common.Address`
4.1.2.2   | `eth_call` MUST NOT accept `from` hex strings with invalid characters
4.1.2.2.1 | `eth_call` SHOULD throw error `-32602` [!] on improper hex string and return message `invalid argument 0: json: cannot unmarshal invalid hex string into Go struct field CallArgs.from of type common.Address`
4.1.2.3   | `eth_call` MUST consider CALLER account to equal a 32 byte hex string [!] of the `from` parameter
4.1.2.3.1 | `eth_call` MUST accept a `from` account that does not exist on-chain
4.1.2.3.2 | `eth_call` MUST consider CALLER account to equal the `from` parameter if the account does not exist on-chain 
4.2       | `eth_call` MUST accept an input parameter `to` of type `DATA` [!]
4.2.1     | `eth_call` MUST accept requests with `to` equal to null
4.2.1.1   | `eth_call` MUST return empty hex string [!] if `to` input parameter is equal to null
4.2.2     | `eth_call` MUST only accept hex encoded address strings as specified by [!] 
4.2.3     | `eth_call` MUST accept requests with `to` defined
4.2.3.1   | `eth_call` MUST consider a `to` parameter that does not exist on-chain to have the same behavior as a `to` parameter equal to null
4.2.3.1.1 | `eth_call` MUST return an empty hex-string [!] if the `to` parameter is defined and does not exist on-chain
4.3       | `eth_call` MUST accept an input parameter `gas` of type `QUANTITY` [!]
4.3.1     | `eth_call` MUST accept requests with `gas` equal to `null` [!]
4.3.1.1   | `eth_call` MUST consider gas to equal 25 million if the `gas` parameter is equal to `null`[!]
4.3.2     | `eth_call` MUST accept requests with `gas` equal to a value greater than block `GAS LIMIT`[!] 
4.3.3     | `eth_call` MUST output `GAS`[!] to equal the `gas` input parameter minus the gas used at `GAS`[!] execution time
4.3.3.1   | `eth_call` MUST output `GAS`[!] to equal `25 million`[!] minus the gas used at `GAS`[!] execution time
4.3.4     | `eth_call` MUST NOT accept requests if the `gas` input parameter is less than `implicit gas`[!] or `actual gas`[!]
4.3.4.1   | `eth_call` SHOULD throw exception `-32000` with message `err: intrinsic gas too low: have 13107, want 21000 (supplied gas 13107)`[!] if the `gas` input parameter is less than `implicit gas`[!]
4.3.4.2   | `eth_call` SHOULD throw exception `-32000` with message `out of gas`
4.3.5     | `eth_call` MUST NOT accept requests if the `gas` input parameter is not properly formatted
4.3.5.1   | `eth_call` SHOULD throw exception `-32602` with message `invalid argument 0: json: cannot unmarshal hex number with leading zero digits into Go struct field CallArgs.gas of type hexutil.Uint64`[!] if the `gas` input parameter does not meet `hex encoded`[!] specifications
4.3.6     | `eth_call` MUST NOT accept requests if the `gas` input parameter is greater than `2^64 - 1` or `0xffffffffffffffff`
4.3.6.1   | `eth_call` SHOULD throw exception `-32602` with message `invalid argument 0: json: cannot unmarshal hex number > 64 bits into Go struct field CallArgs.gas of type hexutil.Uint64` if the `gas` input parameter is greater than the hex string encoded decimal `2^64 - 1`
4.4       | `eth_call` MUST accept an input parameter `gasPrice` of type `Quantity`[!]
4.4.1     | `eth_call` MUST accept a request if `gasPrice` input parameter is equal to `null`[!]
4.4.1.1   | `eth_call` MUST consider `GASPRICE`[!] as equal to 0 if `gasPrice` input parameter is equal to `null`[!]
4.4.2     | `eth_call` MUST consider `GASPRICE`[!] as equal to `gasPrice` input parameter if `gasPrice` input parameter is not equal to null and meets `Quantity` requirements
4.4.2.1   | `eth_call` SHOULD throw exception `-32000` with message `err: insufficient funds for gas * price + value: address {from} have {from account balance} want {gas * gasPrice + value} (supplied gas {gas})` if the `gasPrice` input parameter multiplied by `gas` input parameter added to `value` input paremeter are greater than the balance of the account associated with the `from` input parameter
4.4.2.2   | `eth_call` SHOULD throw exception `-32000` with message `err: insufficient funds for gas * price + value: address 0x0000000000000000000000000000000000000000 have 0 want {gas * gasPrice + value} (supplied gas {gas})` if the `gasPrice` input parameter multiplied by `gas` input parameter added to `value` input paremeter are greater than 0 and the `from` input parameter is equal to null
4.5       | `eth_call` MUST accept an input parameter `value` of type `QUANTITY` [!]
4.5.1     | `eth_call` MUST consider the `BALANCE`[!] of `ADDRESS`[!] to equal the on-chain account balance of the `to` input parameter added to the `value` input parameter
4.5.1.1   | `eth_call` SHOULD throw exception `-32000` with message `err: insufficient funds for transfer: address {to} (supplied gas {gas || 25000000[!]})` if the value of `BALANCE`[!] of `ADDRESS`[!] on-chain added to the `value` input parameter is less than 0
4.5.1.2   | `eth_call` SHOULD throw exception `-32000` with message `err: insufficient funds for transfer: address {from} (supplied gas {gas || 25000000[!]})` if the value of `BALANCE`[!] of `CALLER`[!] on-chain is less than the `value` input parameter
4.5.1.2.1 | `eth_call` SHOULD throw exception `-32000` with message `err: insufficient funds for transfer: address {from} (supplied gas {gas || 25000000[!]})` if the value of `BALANCE`[!] of `CALLER`[!] on-chain is less than the `value` input parameter AND `to` input parameter is equal to `null`[!]
4.5.1.2.2 | `eth_call` SHOULD throw exception `-32000` with message `err: insufficient funds for transfer: address {from} (supplied gas {gas || 25000000[!]})` if the `value` input parameter is greater than 0 AND the `from` input parameter is equal to `null`[!]
5         | `eth_call` MUST accept a `params` parameter [JSON Array](https://tools.ietf.org/html/rfc7159#section-5) of length 2, and its second item (index = 1) containing a `Block Identifier`[!] parameter that specifies the block height of the best block ([yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf)) to assume the state of
5.1       | `eth_call` MUST assume the on-chain state of the latest best block ([yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf)) if the `Block Identifier` parameter is equal to the [JSON String](https://tools.ietf.org/html/rfc7159#section-7) of "latest"; the latest best block height ([yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf)) is equal to the current best block height minus one.
5.2       | `eth_call` MUST assume the on-chain state of the current best block with the greatest height ([yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf))  if the `Block Identifier` parameter is equal to the [JSON String](https://tools.ietf.org/html/rfc7159#section-7) of "pending"; the pending best block height ([yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf)) is equal to the current best block height.
5.3       | `eth_call` MUST assume the on-chain state of the genesis best block ([yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf)) if the `Block Identifier` parameter is equal to the [JSON String](https://tools.ietf.org/html/rfc7159#section-7) of "earliest"; the earliest best block height ([yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf)) is equal to 0.
5.4       | `eth_call` MUST assume the on-chain state of the best blockchain block with height equal to the `Quantity`[!] value of the `Block Identifier` parameter if the `Block Identifier` parameter is equal to a hex encoded `Quantity`[!] value. Height is equal to the number of blocks after the genesis block on the best blockchain (block number).
5.5       | `eth_call` SHOULD throw exception `-32602` [1] with message `invalid argument 1: hex string without 0x prefix` if the provided `Block Identifier` parameter is neither a [JSON String](https://tools.ietf.org/html/rfc7159#section-7) value equal to `earliest`, `latest`, `pending` nor a hex encoded `Quantity`[!] value.
5.6       | `eth_call` SHOULD throw exception `-32000` [1] with message `invalid arguments; neither block nor hash specified` if the provided `Block Identifier` parameter is either not defined or equal to `null`[!].
5.7       | `eth_call` SHOULD throw exception `-32000` [1] with message `head not found` if the `Block Identifier` parameter is equal to a hex encoded `Quantity`[!] value greater than the currently known height of the best blockchain ([yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf))

# Tests
[...]

# Security Considerations
[?]

# Notes About Usage

## Summary
`eth_call` is useful for development and avoiding failed transactions. `eth_call` Executes a new message call immediately without submitting a transaction to the network

## Parameters

|#|Type|Description|
|-|-|-|
|1|{`object`}|@property {[`Data`](#data)} `[from]` - transaction sender<br/>@property {[`Data`](#data)} `to` - transaction recipient or `null` if deploying a contract<br/>@property {[`Quantity`](#quantity)} `[gas]` - gas provided for transaction execution<br/>@property {[`Quantity`](#quantity)} `[gasPrice]` - price in wei of each gas used<br/>@property {[`Quantity`](#quantity)} `[value]` - value in wei sent with this transaction<br/>@property {[`Data`](#data)} `[data]` - contract code or a hashed method call with encoded args|
|2|{[`Quantity`]()[!]\|`string`\|[`Block Identifier`]()[!]}|block number, or one of `"latest"`, `"earliest"` or `"pending"`, or a block identifier as described in [`Block Identifier`](#block-identifier)|

## Returns

{[`Data`][!]} - return value of executed contract

# Example

```sh
# Request
curl -X POST --data '{
    "id": 1337,
    "jsonrpc": "2.0",
    "method": "eth_call",
    "params": [{
        "data": "0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675",
        "from": "0xb60e8dd61c5d32be8058bb8eb970870f07233155",
        "gas": "0x76c0",
        "gasPrice": "0x9184e72a000",
        "to": "0xd46e8dd67c5d32be8058bb8eb970870f07244567",
        "value": "0x9184e72a"
    }]
}' <url>

# Response
{
    "id": 1337,
    "jsonrpc": "2.0",
    "result": "0x"
}
```

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
