
Env Section
===========

::

        "env" : {
            "currentCoinbase" : "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
            "currentDifficulty" : "0x020000",
            "currentGasLimit" : "0xff112233445566",
            "currentNumber" : "0x01",
            "currentTimestamp" : "0x03e8",
            "previousHash" : "0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6"
        },

Env section describe information required to construct a genesis block, or VM env for transaction execution.

* The fields are always 0x prefixed HEX.

**Fields**

======================= ===============================================================================
``currentCoinbase``      author/miner/coinbase address
``currentDifficulty``    transaction executed in a block with this difficulty
``currentGasLimit``      transaction executed in a block with this gas limit
``currentNumber``        transaction executed in a block with this number
``currentTimestamp``     transaction executed in a block with this timestamp
``previousHash``         hash of the previous block (deprecated)
======================= ===============================================================================