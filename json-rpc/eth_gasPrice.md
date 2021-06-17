# `Eth_gasPrice`
The key words “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in [RFC-2119](https://www.ietf.org/rfc/rfc2119.txt).
Specification | Description 
---|---
1 |Eth_gasPrice Must return price per gas in wei as type quantity|
1.1 |Eth_gasPrice must return initial price per gas if there is no information from past transactions|
1.11|Eth_gasPrice must set initial price per gas before receiving any transactions|
1.111|Eth_gasPrice's initial pric per gas May be set to 1 |
1.1111 |Eth_gasPrice must set gasPrice to the gasPrice of the first transaction right away if the initial price per gas is 1|
1.2 |Eth_gasPrice may use a client defined method to estimate gasPrice if there is enough transaction data|
2 |Eth_gasPrice must consider a max gas price|
2.1 |Eth_gasPrice max gas price must be within the range of 0x1 to 0x7FFFFFFFFFFFFFFF|
2.2 |Eth_gasPrice must return the max gas price if transaction gasPrice is more than the max gas price|
2.21 |Eth_gasPrice max gas price must be predefined or default|

# Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
