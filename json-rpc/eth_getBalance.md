# `Eth_getBalance`
The key words “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in [RFC-2119](https://www.ietf.org/rfc/rfc2119.txt).
Specification | Description 
---|---
1|Eth_getBalance must be sent a valid Ethereum address as the first parameter|
1.1 |Eth_getBalance should return error code -32602 "invalid argument 0: json: cannot unmarshal hex string of odd length into Go value of type common.Address" if the address send has an odd length|
1.2 |Eth_getBalance should return error code -32602 "invalid argument 0: hex string has length n, want 40 for common.Address" if address length is even but not equal to 40|
1.3 |Eth_getBalance should return error code -32602  "invalid argument 0: json: cannot unmarshal hex string without 0x prefix into Go value of type common.Address" if the address is blank or a random string|
2 |Eth_getBalnace must be sent the block that you want the balance from as the second parameter|
2.1|Eth_getBalance must accept block numbers as hex string "0xa" block 10, "0xf5f" block 3935|
2.1.1 |Eth_getBalance should return error code -32602 "invalid argument 1: hex string \"0x\""  if it receives an incomplete  hex string|
2.1.2 |Eth_getBalance should return  error code -32000 "header not found" if block does not exist|
2.2 |Eth_getBalance must also accept the tags "latest" "earliest" "pending"|
2.2.1 |Eth_getBalance should return error code -32602 "invalid argument 1: hex string without 0x prefix" if it receives a string that is not "latest", "earliest", or "pending"|
3 |Eth_getBalance must return the balance of the account in wei as type quantity|
# Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
