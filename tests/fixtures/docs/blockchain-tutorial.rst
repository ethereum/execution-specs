.. blockchain-tests-tutorial:

###########################################
Blockchain Tests
###########################################
`Ori Pomerantz <mailto://qbzzt1@gmail.com>`_

In this tutorial you learn how to use the skills you learned writing state tests to write
blockchain tests. These tests can include multiple blocks and each of those blocks can include
multiple transactions.

The Environment
===============
Before you start, make sure you create the retesteth tutorial and create the 
environment explained there. Also make sure you read and understand the state
transition tests tutorial.


Types of Blockchain Tests
=========================
If you go to **tests/src/BlockchainTestsFiller** you will see three different directories.

- **ValidBlocks** are tests that only have valid blocks, which the client should accept.

- **InvalidBlocks** are tests that should raise an exception because they 
  include invalid blocks.

- **TransitionTests** are tests that verify the transitions between different 
  versions of the Ethereum protocol (called `forks 
  <https://medium.com/mycrypto/the-history-of-ethereum-hard-forks-6a6dae76d56f>`_) 
  are handled correctly. These tests are very important, but the people who write 
  them are typically the people who write the tests software so I am not going to 
  explain them here.
   

Valid Block Tests
=================
There is a valid block test in `tests/docs/tutorial_samples/05_simpleTxFiller.yml 
<https://github.com/ethereum/tests/blob/develop/docs/tutorial_samples/05_simpleTxFiller.yml>`_.
We copy it to **bcExample**.

::

   mkdir ~/tests/src/Blo*/Val*/bcExample*
   cp ~/tests/docs/tu*/05_* ~/tests/src/Blo*/Val*/bcExample*
   cd ~
   ./dretesteth.sh -t BlockchainTests/ValidBlocks/bcExample  -- \
       --testpath ~/tests --datadir /tests/config --filltests \
       --singletest 05_simpleTx


Test Source Code
----------------
This section explains **05_simpleTxFiller.yml**. I am only going to document
the things in which it is different from state transition tests.

State transition tests take their 
`genesis block <https://arvanaghi.com/blog/explaining-the-genesis-block-in-ethereum/>`_
from the client configuration (or, failing that, from the default client configuration)
in **retesteth**. In blockchain tests the values may be relevant to the test, so
you specify them directly.

::

  genesisBlockHeader:
    bloom: '0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    coinbase: '0x8888f1f195afa192cfee860698584c030f4c9db1'
    difficulty: '131072'
    extraData: '0x42'
    gasLimit: '3141592'
    gasUsed: '0'
    mixHash: '0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421'
    nonce: '0x0102030405060708'
    number: '0'
    parentHash: '0x0000000000000000000000000000000000000000000000000000000000000000'
    receiptTrie: '0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421'
    stateRoot: '0xf99eb1626cfa6db435c0836235942d7ccaa935f1ae247d3f1c21e495685f903a'
    timestamp: '0x54c98c81'
    transactionsTrie: '0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421'
    uncleHash: '0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347'

In a lot of existing tests you will see a definition for **sealEngine**. This is
related to getting a proof of work as part of the test. However, this is no longer
part of **retesteth**, so you can omit it or set it to **NoProof**.

::

  #  sealEngine: NoProof

Instead of a single transaction, we have a list of blocks. In a YAML list you 
tell different items apart by the dash character (**-**). The block list has two items in it.

::

  blocks:

The first block has one field, **transactions**, a list of transactions. 
Every individual transaction is specified with the same fields used in
state transition tests. This block only has one transaction, which transfers
10 Wei.

::

  - transactions:
    - data: ''
      gasLimit: '50000'
      gasPrice: '10'


This is the **nonce** value for the transaction. The first value is the 
**nonce** associated with the address in the **pre:** section. 
Each subsequent transaction from the same address increments the **nonce**.

Alternatively, if you use **auto** for every transaction of an account, 
the retesteth tool will provide the nonce values automatically.

::

      nonce: '0'
      secretKey: 45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
      to: 0xde570000de570000de570000de570000de570000
      value: '10'

This is the second block. In contrast to the first block, in this one we specify
a **blockHeader** and override some of the default values.

::

  - blockHeader:
      gasLimit: '3141592'

A block can also contain references to `uncle blocks (blocks mined at the same
time) <https://www.investopedia.com/terms/u/uncle-block-cryptocurrency.asp>`_.
Note that writing tests with uncle headers is complicated, because you need
to run the test once to get the correct hash value. Only then can you put the
correct value in the test and run it again so it'll be successful.

::

    uncleHeaders: []


This block has two transactions.

::

    transactions:
    - data: ''
      gasLimit: '50000'
      gasPrice: '20'


This is another transaction from the same address, so the **nonce** is one more 
than it was in the previous one.

::

      nonce: '1'
      secretKey: 45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
      to: 0xde570000de570000de570000de570000de570000
      value: '20'
    - data: ''
      gasLimit: '50000'
      gasPrice: '30'


This transaction comes from a different address (addresses are uniquely derived
from the private key, and this one is different from the one in the previous
transcation). This transaction's **nonce** value is the initial value for 
that address, zero.

::

      nonce: '0'
      secretKey: 41f6e321b31e72173f8ff2e292359e1862f24fba42fe6f97efaf641980eff298
      to: 0xde570000de570000de570000de570000de570000
      value: '30'


.. _invalid-block-tests:

Invalid Block Tests
===================

The invalid block test is in `tests/docs/tutorial_samples/06_invalidBlockFiller.yml 
<https://github.com/ethereum/tests/blob/develop/docs/tutorial_samples/06_invalidBlockFiller.yml>`_
We copy it to **bcExample**.


::
 
   mkdir ~/tests/src/BlockchainTestsFiller/InvalidBlocks/bcExample
   cp ~/tests/docs/tutorial_samples/06_* ~/tests/src/Bl*/In*/bcExample*
   cd ~
   ./dretesteth.sh -t BlockchainTests/InvalidBlocks/bcExample  -- \
       --testpath ~/tests --datadir /tests/config --filltests \
       --singletest 06_invalidBlock


Invalid block tests contain invalid blocks, blocks that
cause a client to raise an exception. To tell **retesteth** which exception 
should be raised by a block, we add an **expectException** field to the 
**blockHeader**. In that field we put the different forks the test 
supports, and the exception we expect to be raised in them:

::

  - blockHeader:
      gasLimit: '30'
      expectException:
        Istanbul: TooMuchGasUsed
        Berlin: TooMuchGasUsed


.. warning::

   The **expectException** field is only used when **\\-\\-filltests** is specified.
   When it is not, **retesteth** just expects the processing of the block to fail,
   without ensuring the exception is the correct one. The reason for this feature 
   is that not all clients tells us the exact exception type when they reject a
   block as invalid.



Getting Exception Names
-----------------------
If you don't know what exception to expect, run the test without an **expectException**.
The output will include an error message similar to this one:

::

   Error: Postmine block tweak expected no exception! Client errors with: 
   'Error importing raw rlp block: Invalid gasUsed: header.gasUsed > header.gasLimit' 
   (bcBlockGasLimitTest/06_invalidBlock_Berlin, fork: Berlin, chain: default, block: 2)

Then took in **tests/conf/<name of client>/config** and look for the first few words
of the error message. For example, in **tests/conf/tn8tool/config** we find
this line:

::

      "TooMuchGasUsed" : "Invalid gasUsed:",

This tells us that the exception to expect is **TooMuchGasUsed**.


Conclusion
==========
You should now be able to write most types of Ethereum tests. If you still have 
questions, you can look in the reference section or e-mail for help.
