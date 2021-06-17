# `eth_gasPrice`
The key words “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in [RFC-2119](https://www.ietf.org/rfc/rfc2119.txt).
Specification | Description 
---|---
1 |eth_gasPrice MUST return price per gas unit in wei as type quantity|
1.1|eth_gasPrice MUST return price per gas unit predefined by client if it has not received any transactions|
1.1.1|eth_gasPrice's Client predefined price per gas unit MUST be greater than 0|
1.2 |eth_gasPrice MAY use a client defined method to estimate gasPrice if there is enough transaction data|
2 |eth_gasPrice MUST consider a max price per gas unit|
2.1 |eth_gasPrice max price per gas unit MUST be predefined by client|
2.1.1 |eth_gasPrice max price per gas unit MAY be set by user before initializing client|
2.2 |eth_gasPrice max price per gas unit MUST be within the range of 0x1 to 0x7FFFFFFFFFFFFFFF|

# Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
