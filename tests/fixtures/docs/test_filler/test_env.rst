Env
==============
This section contains the environment, the block just before the one that runs
the VM or executes the transaction.

Format
------

.. list-table::
   :header-rows: 1

   * - JSON

     - YAML

   * -

       ::

           {
              "name-of-test": {
                 <other sections>,
                 "env" : {
                    "currentCoinbase" : "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
                    "currentDifficulty" : "0x020000",
                    "currentGasLimit" : "0x05f5e100",
                    "currentNumber" : "0x01",
                    "currentTimestamp" : "0x03e8",
                    "previousHash" : "0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6",,
                    "currentBaseFee" : "1000"
                 }
              }
           }

     -

       ::

           name-of-test:
              <other sections>
              env:
                 currentCoinbase: 2adc25665018aa1fe0e6bc666dac8fc2697ff9ba
                 currentDifficulty: 0x20000
                 currentGasLimit: 100000000
                 currentNumber: 1
                 currentTimestamp: 1000
                 previousHash: 5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6
                 currentBaseFee: 1000


Fields
------
`You can read the definition of Ethereum block header fields here
<https://medium.com/@derao512/ethereum-under-the-hood-part-7-blocks-7f223510ba10>`_.

Note that this section only contains the fields that are relevant to single
transaction tests.

=================== ========================
Name in Env Section Meaning
=================== ========================
currentCoinbase     beneficiary of mining fee
currentDifficulty   difficulty of previous block
currentGasLimit     limit of gas usage per block
currentNumber       number of ancestory blocks
currentTimestamp    `Unix time <https://en.wikipedia.org/wiki/Unix_time>`_
previousHash        hash of previous block
currentBaseFee      London and afterwards, the 
                    `block base fee <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1559.md>`_
=================== ========================
