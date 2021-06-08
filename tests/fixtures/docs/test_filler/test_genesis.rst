Genesis Block
==============
This section contains the genesis block that starts the chain being tested.


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
                 genesisBlockHeader: {
                    "bloom" : "0x0 <<lots more 0s>>"
                    "coinbase" : "0x8888f1f195afa192cfee860698584c030f4c9db1",
                    "difficulty" : "0x020000",
                    "extraData" : "0x42",
                    "gasLimit" : "0x2fefd8",
                    "gasUsed" : "0x00",
                    "mixHash" : "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "nonce" : "0x0000000000000000",
                    "number" : "0x00",
                    "parentHash" : "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "receiptTrie" : "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
                    "stateRoot" : "0x14f0692d8daa55f0eb56a1cf1e2b07746d66ddfa3f8bae21fece76d1421b5d47",
                    "timestamp" : "0x54c98c81",
                    "transactionsTrie" : "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
                    "uncleHash" : "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
                    "baseFee" : "1000"
                 }
              }
           }

     -

       ::

           name-of-test:
              <other sections>
              genesisBlockHeader:
                 bloom: 0x0 <<lots more 0s>>
                 coinbase: 0x8888f1f195afa192cfee860698584c030f4c9db1
                 difficulty: 131072
                 extraData: 0x42
                 gasLimit: 3141592
                 gasUsed: 0
                 mixHash: 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421
                 nonce: 0x0102030405060708
                 number: 0
                 parentHash: 0x0000000000000000000000000000000000000000000000000000000000000000
                 receiptTrie: 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421
                 stateRoot: 0xf99eb1626cfa6db435c0836235942d7ccaa935f1ae247d3f1c21e495685f903a
                 timestamp: 0x54c98c81
                 transactionsTrie: 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421
                 uncleHash: 0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347
                 baseFee: 1000

Fields
------
.. include:: ../test_filler/test_blockheader.rst
