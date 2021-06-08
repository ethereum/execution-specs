.. _blockchain_filler:

=================================
Blockchain Tests Source Code
=================================
Location: `/src/BlockchainTestsFiller
<https://github.com/ethereum/tests/tree/develop/src/BlockchainTestsFiller>`_

Blockchain tests can include multiple blocks and each of those blocks can include 
multiple transactions. These blocks can be either valid or invalid.



Subfolders
==========

================= ========================================
InvalidBlocks     Tests containing blocks that are expected to fail on import
ValidBlocks       Normal blockchain tests
TransitionTests   Blockchain tests with exotic network rules switching forks at block #5
================= ========================================

.. bc_src:
.. include:: ../test_filler/test_src.rst


.. _bc_struct:
.. include:: ../test_filler/test_structure.rst


.. _struct_bc_genesis:
.. include:: ../test_filler/test_genesis.rst


.. _struct_bc_pre:
.. include:: ../test_filler/test_pre.rst


.. _struct_bc_blocks:
.. include:: ../test_filler/test_blocks.rst


.. _struct_bc_transaction:
.. include:: ../test_filler/test_transaction_blockchain.rst


.. _struct_bc_expect:
.. include:: ../test_filler/test_expect_blockchain.rst


