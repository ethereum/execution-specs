
# `Quantity`
The key words “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in [RFC-2119](https://www.ietf.org/rfc/rfc2119.txt).
| Req. | Description  |
| ----------- | ------------ |
| 1   | A `Quantity` value **MUST** be hex-encoded |
| 2   | A `Quantity` value **MUST** be "0x"-prefixed |
| 3   | A `Quantity` value **MUST** be expressed using the fewest possible hex digits per byte |
| 4   | A `Quantity` value **MUST** express zero as "0x0" |
| 5   | A `Quantity` value **MUST** represent an unsigned integer value |
| 6   | A `Quantity` value **MUST** represent a 32 byte hex encoded decimal with the leading `0`s stripped |

# Notes About Usage
### Description
`Quantity` is the 32 byte hex-encoded representation of a decimal value

### Examples 

|Value|Valid|Reason|
|-|-|-|
|0x|`invalid`|empty not a valid quantity|
|0x0|`valid`|interpreted as a quantity of zero|
|0x00|`invalid`|leading zeroes not allowed|
|0x41|`valid`|interpreted as a quantity of 65|
|0x400|`valid`|interpreted as a quantity of 1024|
|0x0400|`invalid`|leading zeroes not allowed|
|ff|`invalid`|values must be prefixed|
