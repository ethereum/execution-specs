# Description
`Quantity` is the 32 byte hex-encoded representation of a decimal value

# Specification

| Req. | Description  |
| ----------- | ------------ |
| 1   | A `Quantity` value **MUST** be hex-encoded |
| 2   | A `Quantity` value **MUST** be "0x"-prefixed |
| 3   | A `Quantity` value **MUST** be expressed using the fewest possible hex digits per byte |
| 4   | A `Quantity` value **MUST** express zero as "0x0" |
| 5   | A `Quantity` value **MUST** represent an unsigned integer value |
| 6   | A `Quantity` value **MUST** represent a 32 byte hex encoded decimal with the leading `0`s stripped |

# Examples 

|Value|Valid|Reason|
|-|-|-|
|0x|`invalid`|empty not a valid quantity|
|0x0|`valid`|interpreted as a quantity of zero|
|0x00|`invalid`|leading zeroes not allowed|
|0x41|`valid`|interpreted as a quantity of 65|
|0x400|`valid`|interpreted as a quantity of 1024|
|0x0400|`invalid`|leading zeroes not allowed|
|ff|`invalid`|values must be prefixed|
