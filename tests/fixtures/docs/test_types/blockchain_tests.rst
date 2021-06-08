.. _blockchain_tests:

==========================
Generated Blockchain Tests
==========================

Location `/BlockchainTests <https://github.com/ethereum/tests/tree/develop/BlockchainTests>`_

**Subfolders**

================= ========================================
GeneralStateTests Tests generated in blockchain form from GeneralStateTests
InvalidBlocks     Tests containing blocks that are expected to fail on import
ValidBlocks       Normal blockchain tests
TransitionTests   BC tests with exotic network rules switching forks at block#5
================= ========================================


Test Structure
==============

Contains **blocks** that are to be imported on top of **genesisRLP** of network fork rules **network** using sealEngine **NoProof** (Ethash no longer supported) and having genesis state as **pre**.

The result of block import must be state **postState** or **postStateHash** if  result state is too big. And the last block of chain with maxTotalDifficulty must be block with hash **lastblockhash**

Single blockchain test file might contain many tests as there are many test generations for each individual **network** fork rules from single test source.

::

  {
     "testname": {
       "_info" : { ... },
       "sealEngine": [ "NoProof" | "Ethash" ]
       "network": "Byzantium",
       "pre": { ... },
       "genesisBlockHeader": { ... },
       "genesisRLP": " ... ",
       "blocks" : [ ... ],
       "postState": { ... },
       "lastblockhash": " ... "
     },
     "testname": {
       "_info" : { ... },
       "sealEngine": [ "NoProof" | "Ethash" ]
       "network": "Byzantium",
       "pre": { ... },
       "genesisBlockHeader": { ... },
       "genesisRLP": " ... ",
       "blocks" : [ ... ],
       "postStateHash": " ... ",
       "lastblockhash": " ... "
     }
     ...
  }

.. _info_bctest:
.. include:: ../test_types/TestStructures/info.rst
.. _pre_bctest:
.. include:: ../test_types/TestStructures/pre.rst
.. _genesisblockheader_bctest:
.. include:: ../test_types/TestStructures/BlockchainTests/genesisblockheader.rst
.. _block_bctest:
.. include:: ../test_types/TestStructures/BlockchainTests/block.rst
.. _transaction_vrs_bctest:
.. include:: ../test_types/TestStructures/transaction.rst

