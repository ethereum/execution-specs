# Common Types

## Basic Types

### `Address`

[Bytes](#bytes) of a 20-byte fixed length.

### `Bloom`

[Bytes](#bytes) of a 256-byte fixed length.

### `Bytes`

Hexadecimal representation of binary data of any length encoded as a JSON string, with a "0x" prefix.

### `EmptyAddress`

An empty JSON string `""`, used to represent an empty address. E.g. in the `to` field of a transaction when it is a contract creation.

### `Hash`

[Bytes](#bytes) of a 32-byte fixed length.

### `HeaderNonce`

[Bytes](#bytes) of a 8-byte fixed length.

### `HexNumber`

Hexadecimal number with "0x" prefix encoded as a JSON string.

### `List`

A JSON array where each element is a specific type, also defined in this document.
E.g. `List[Address]` is a JSON array where each element is an Ethereum address.

### `Mapping`

A JSON object where the keys and values are specific types, also defined in this document.
E.g. `Mapping[Address, Account]` is a JSON object where the keys are Ethereum addresses, and the values are Ethereum accounts.

### `Number`

Decimal number encoded as a JSON string.

### `Optional`

Marks a field as optional, meaning that the field can be missing from the JSON object.

### `ZeroPaddedHexNumber`

Hexadecimal number with "0x" prefix encoded as a JSON string, with a single zero used to pad odd number of digits, and zero represented as "0x00".

## Composite Types

### `Storage`: [`Mapping`](#mapping)`[`[`Hash`](#hash)`,`[`Hash`](#hash)`]`

Storage represented as a JSON object, where the keys and values are represented with the [`Hash`](#hash) type.

### `Account`

An Ethereum account represented as a JSON object with the following fields:

#### - `balance`: [`ZeroPaddedHexNumber`](#zeropaddedhexnumber)

Balance of the account.

#### - `nonce`: [`ZeroPaddedHexNumber`](#zeropaddedhexnumber)

Nonce of the account.

#### - `code`: [`Bytes`](#bytes)

Code of the account.

#### - `storage`: [`Storage`](#storage-mappinghashhash)

Storage of the account.

### `Alloc`: [`Mapping`](#mapping)`[`[`Address`](#address)`,`[`Account`](#account)`]`

State allocation represented as a JSON object, where the keys are the addresses of the accounts, and the values are the accounts.

### `BlobSchedule`: [`Mapping`](#mapping)`[`[`Fork`](#fork)`,`[`ForkBlobSchedule`](#forkblobschedule)`]`

Maps forks to blob schedule configurations as defined by [EIP-7840](https://eips.ethereum.org/EIPS/eip-7840).

### `Environment`

Contains blockchain-related configuration that provides the context in which a test is run.

### `ForkBlobSchedule`

A fork blob schedule as defined by [EIP-7840](https://eips.ethereum.org/EIPS/eip-7840) as a JSON dictionary with the following entries:

#### - `target`: [`ZeroPaddedHexNumber`](#zeropaddedhexnumber)

The target blob count for a block.

#### - `max`: [`ZeroPaddedHexNumber`](#zeropaddedhexnumber)

The maximum possible blob count for a block.

#### - `base_fee_update_fraction`: [`ZeroPaddedHexNumber`](#zeropaddedhexnumber)

The blob base fee update fraction (adjusts the responsiveness of blob gas pricing per fork).

## Fork

Fork type is represented as a JSON string that can be set to one of the following values:

### `"Frontier"`

- Chain ID: `0x00`

### `"Homestead"`

- Chain ID: `0x01`
- Homestead Block: `0x00`

### `"Byzantium"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`

### `"Constantinople"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`

### `"ConstantinopleFix"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`

### `"Istanbul"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`

### `"MuirGlacier"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`

### `"Berlin"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`

### `"BerlinToLondonAt5"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`
- London Block: `0x05`

### `"London"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`
- London Block: `0x00`

### `"ArrowGlacier"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`
- London Block: `0x00`
- Arrow Glacier Block: `0x00`

### `"GrayGlacier"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`
- London Block: `0x00`
- Arrow Glacier Block: `0x00`
- Gray Glacier Block: `0x00`

### `"Merge"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`
- London Block: `0x00`
- Arrow Glacier Block: `0x00`
- Gray Glacier Block: `0x00`
- Terminal Total Difficulty: `0x00`

### `"MergeToShanghaiAtTime15k"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`
- London Block: `0x00`
- Arrow Glacier Block: `0x00`
- Gray Glacier Block: `0x00`
- Terminal Total Difficulty: `0x00`
- Shanghai Time: `0x3a98`

### `"Shanghai"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`
- London Block: `0x00`
- Arrow Glacier Block: `0x00`
- Gray Glacier Block: `0x00`
- Terminal Total Difficulty: `0x00`
- Shanghai Time: `0x00`

### `"ShanghaiToCancunAtTime15k"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`
- London Block: `0x00`
- Arrow Glacier Block: `0x00`
- Gray Glacier Block: `0x00`
- Terminal Total Difficulty: `0x00`
- Shanghai Time: `0x0`
- Cancun Time: `0x3a98`

### `"Cancun"`

- Chain ID: `0x01`
- Homestead Block: `0x00`
- EIP150 Block: `0x00`
- EIP155 Block: `0x00`
- EIP158 Block: `0x00`
- DAO Fork Block: `0x00`
- Byzantium Block: `0x00`
- Constantinople Block: `0x00`
- Constantinople Fix Block: `0x00`
- Istanbul Block: `0x00`
- Muir Glacier Block: `0x00`
- Berlin Block: `0x00`
- London Block: `0x00`
- Arrow Glacier Block: `0x00`
- Gray Glacier Block: `0x00`
- Terminal Total Difficulty: `0x00`
- Shanghai Time: `0x00`
- Cancun Time: `0x00`
