VM tests
========

VM tests test one instance of EVM (which contains one stack of 256-bit words, and one memory space).

Operations accessing the world state should be tested in GeneralStateTests or BlockchainTests instead of in VM tests.

So VM tests should not contain

* `BALANCE`
* `CREATE`
* `CREATE2`
* `CALL`
* `CALLCODE`
* `STATICCALL`
* `DELEGATECALL`
* `EXTCODESIZE`
* `EXTCODECOPY`
* `BLOCKHASH`

Previously, some VM tests contained these, and clients were supposed to implement some mock of the world state (especially, the block hash of a block is supposed to be the hash of the block number).