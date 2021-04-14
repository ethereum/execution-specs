---
title: JSPON RPC Quantity Type Spec
author: Alita Moore (@alita-moore)
discussions-to: https://github.com/ethereum-oasis/eth1.x-JSON-RPC-API-standard
created: 2021-04-13
---

# `Quantity`

##### Description

`Quantity` represents the 

##### Requirements

| Req. | Description  |
| ----------- | ------------ |
|    **Γ1**   | A `Quantity` value **MUST** be hex-encoded |
|    **Γ2**   | A `Quantity` value **MUST** be "0x"-prefixed |
|    **Γ3**   | A `Quantity` value **MUST** be expressed using the fewest possible hex digits per byte |
|    **Γ4**   | A `Quantity` value **MUST** express zero as "0x0" |

##### Examples 

|Value|Valid|Reason|
|-|-|-|
|0x|`invalid`|empty not a valid quantity|
|0x0|`valid`|interpreted as a quantity of zero|
|0x00|`invalid`|leading zeroes not allowed|
|0x41|`valid`|interpreted as a quantity of 65|
|0x400|`valid`|interpreted as a quantity of 1024|
|0x0400|`invalid`|leading zeroes not allowed|
|ff|`invalid`|values must be prefixed|
