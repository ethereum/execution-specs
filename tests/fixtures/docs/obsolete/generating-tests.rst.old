
==========================
Generating Consensus Tests
==========================

.. warning:: This guide targets Linux users.  It might work on Mac OS X.  It will probably not work on Windows.


Consensus Tests
===============
(aka State Transition Tests)

Consensus tests are test cases for all Ethereum implementations. The test cases are distributed in the "Filled" form, which contains, for example, the expected state root hash after transactions. The filled test cases are usually not written by hand, but generated from "test filler" files. ``retesteth`` executable in combination with test protocol supporting clients (``Geth``, ``Besu``, ``Geth-t8ntool``) can convert test fillers into test cases.

When you add a test case in the consensus test suite, you are supposed to push both the filler and the filled test cases into the `tests repository`_.

.. _`tests repository`: https://github.com/ethereum/tests



Preparing the test tools
===========================

For generating consensus tests, an executable ``retesteth`` is necessary.  Moreover, ``retesteth`` uses the LLL compiler when it generates consensus tests.


Option 1: Using the docker image
--------------------------------

.. _`install Docker`: https://www.docker.com/community-edition

.. note::
   Retesteth docker instruction docs are coming up!

.. note::
   Some problems with running the ``retesteth`` command can be fixed by adding the ``--all`` option at the end.


Option 2: Building locally
--------------------------
.. _retesteth: https://github.com/ethereum/retesteth
.. _solidity: https://github.com/winsvega/solidity
.. _`Retesteth`: https://github.com/ethereum/retesteth
.. _`Solidity`: https://github.com/winsvega/solidity
.. _`Tests`: https://github.com/ethereum/tests

Get the following tools and compile it according to the build instructions:

============== ====================================
 `Retesteth`_  Test generator
 `Solidity`_   lll code to evm bytecode translator
 `Tests`_      Ethereum tests repository
============== ====================================

Once setup, create environment variable (so to skip --testpath command for retesteth)

.. code:: bash

    // Given that you cloned repos to ~/Ethereum
    // Add line replacing the path to the test repository you cloned
    sudo nano /etc/environment
    ETHEREUM_TEST_PATH="/home/user/Ethereum/tests"

    // Add lllc to system executables
    sudo ln -s /home/user/Ethereum/solidity/build/lllc/lllc /bin/lllc

    // Add retesteth to system executables (optional)
    sudo ln -s /home/user/Ethereum/retesteth/build/retesteth/retesteth /bin/retesteth
    
    // Reboot for the changes to take effect


Generating a GeneralStateTest Case
==================================

.. note::
    Additional wiki on retesteth commands and test generation:
    https://github.com/ethereum/retesteth/wiki/Retesteth-commands
    https://github.com/ethereum/retesteth/wiki/Creating-a-State-Test-with-retesteth

Designing a Test Case
---------------------

For creating a new GeneralStateTest case, you need:

* environmental parameters
* a transaction
* a state before the transaction (pre-state)
* some expectations about the state after the transaction

For an idea, peek into `an existing test filler`_ under ``src/GeneralStateTestsFiller`` in the tests repository.

.. _`an existing test filler`: https://github.com/ethereum/tests/blob/develop/src/GeneralStateTestsFiller/stExample/add11Filler.json


Usually, when a test is about an instruction, the pre-state contains a contract with a code containing the instruction.  Typically, the contract stores a value in the storage, so that the instruction's behavior is visible in the storage in the expectation.

The code can be written in EVM bytecode or in LLL.

.. note::
   ``retesteth`` cannot understand LLL if the system does not have the LLL compiler installed. The LLL compiler is currently distributed as part of the `Solidity`_ compiler.


Writing or modifying a Test Filler
----------------------------------

A test filler file should always correspond to one test case, so a single GeneralStateTest filler file is not supposed to contain multiple tests.  ``retesteth`` tool still accepts multiple GeneralStateTest fillers in a single test filler file, but this might change.

In the ``tests`` repository, the test filler files for GeneralStateTests live under ``src/GeneralStateTestsFiller`` directory. The directory has many subdirectories. You need to choose one of the subdirectories or create one.  The name of the filler file needs to end with ``Filler.json``.  For example, we might want to create a new directory ``src/GeneralStateTestsFiller/stExample2`` with a new filler file ``returndatacopy_initialFiller.json``, or edit one of the existing filler files in the directory structure.

.. note::
   If you create a new directory here, you need to register it in ``retesteth`` codebase and file a PR.

For creating a new test filler, the easiest way to start is to copy an existing filler file. The first thing to change  is the name of the test in the beginning of the file. The name of the test should coincide with the file name except ``Filler.json`` [#]_. For example, in the file we created above, the filler file contains the name of the test ``returndatacopy_initial``.  The overall structure of ``returndatacopy_initialFiller.json`` should be:

.. code::

   {
       "returndatacopy_initial" : {
          "env" : { ... }
          "expect" : [ ... ]
          "pre" " { ... }
          "transaction" : { ... }
       }
   }


where ``...`` indicates omissions.

.. [#] The file name and the name written in JSON should match because ``retesteth`` prints the name written in JSON, but the user needs to find a file.


``env`` field contains some parameters in a straightforward way (see also advanced section below).

``pre`` field describes the pre-state account-wise:

.. code::

     "pre" : {
        "0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6" : {
            "balance" : "0x0de0b6b3a7640000",
            "code" : "{ (MSTORE 0 0x112233445566778899aabbccddeeff) (RETURNDATACOPY 0 0 32) (SSTORE 0 (MLOAD 0)) }",
            "// code" : "You can use commented out attribute names for additional comments",
            "nonce" : "0x00",
            "storage" : {
                "0x00" : "0x01"
            }
        }
     }


As specified in the Yellow Paper, an account contains a balance, a code, a nonce and a storage.

.. note::
   For field descriptions see also the docs on the resulting :ref:`gstate_tests` test format.

.. note::
   The ``env`` section might become deprecated in future state test filler formats.

Unless you are testing malformed bytecode, always try to use ``LLL`` code in the test filler.  ``LLL`` code is easier to understand and to modify.


This particular test expected to see ``0`` in the first slot in the storage. In order to make this change visible, the pre-state has ``1`` there.

Usually, there is another account that acts as the initial caller of the transaction.

``transaction`` field is somehow interesting because it can describe a multidimensional array of test cases.  Notice that ``data``, ``gasLimit`` and ``value`` fields are lists.

.. code::

   "transaction" : {
        "data" : [
            "", "0xaaaa", "0xbbbb"
        ],
        "gasLimit" : [
            "0x0a00000000",
            "0x0"
        ],
        "gasPrice" : "0x01",
        "nonce" : "0x00",
        "secretKey" : "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8",
        "to" : "0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
        "value" : [
            "0x00"
        ]
    }


Since ``data`` has three elements and ``gasLimit`` has two elements, the above ``transaction`` field specifies six different transactions.  Later, in the ``expect`` section, ``data : 1`` would mean the ``0xaaaa`` as data, and ``gasLimit : 0`` would mean ``0x0a00000000`` as gas limit.

Moreover, these transactions are tested under different versions of the protocol.

``expect`` field of the filler specifies the expected fields of the state after the transaction.  The ``expect`` field does not need to specify a state completely, but it should specify some features of some accounts.  ``expect`` field is a list. Each element talks about some elements of the multi-dimensional array defined in ``transaction`` field.

.. code::

   "expect" : [
        {
            "indexes" : {
                "data" : 0,
                "gas" : -1,
                "value" : -1
            },
            "network" : ["Frontier", "Homestead"],
            "result" : {
                "095e7baea6a6c7c4c2dfeb977efac326af552d87" : {
                    "balance" : "2000000000000000010",
                    "storage" : {
                        "0x" : "0x01",
                        "0x01" : "0x01"
                    }
                },
                "2adc25665018aa1fe0e6bc666dac8fc2697ff9ba" : {
                    "balance" : "20663"
                },
                "a94f5374fce5edbc8e2a8697c15331677e6ebf0b" : {
                    "balance" : "99979327",
                    "nonce" : "1"
                }
            }
        },
        {
            "indexes" : {
                "data" : 1,
                "gas" : -1,
                "value" : -1
            },
        ...
        }
    ]


``indexes`` field specifies a subset of the transactions.  ``-1`` means "whichever".
``"data" : 0`` points to the first element in the ``data`` field in ``transaction``.

``network`` field is somehow similar.  It specifies the versions of the protocol for which the expectation applies.  For expectations common to all versions, say ``"network" : [">=Frontier"] ( the old ``"network" : ALL`` syntax is not supported any more). As you can see in this example to reference all networks it is also possible to use greater or greater equal syntax like ``"network": [">=Byzantium"]`` to select a subset of forks to generate tests for (here: all forks from ``Byzantium`` onwards). 

.. note::
   Order of forks: ``Frontier`` < ``Homestead`` < ``EIP150`` < ``EIP158`` < ``Byzantium`` < ``Constantinople``

Filling the Test
----------------

The test filler file is not for consumption.  The filler file needs to be filled into a test. ``retesteth`` asks the host client to compute the post-state from the test filler, and produce the test. The advantage of the filled test is that it can catch any post-state difference between clients.

First, if you created a new subdirectory for the filler, you need to edit the source of ``Retesteth`` so that ``retesteth`` recognizes the new subdirectory.  The file to edit is `StateTests.cpp`_, which lists the names of the subdirectories scanned for GeneralStateTest filters.

.. _`StateTests.cpp`: https://github.com/ethereum/aleth/blob/master/test/tools/jsontests/StateTests.cpp


After building ``retesteth``, you are ready to fill the test.


Set the environmental variable ``ETHEREUM_TEST_PATH`` to the directory where ``tests`` repository is checked out, this should be provided as an absolute path:

.. code:: bash
   
   export ETHEREUM_TEST_PATH="<LOCAL_PATH_TO_ETH_TESTS>" 

.. note::
   Depending on your shell, there are various ways to permanently set up ``ETHEREUM_TEST_PATH`` environment variable. For example, adding the export statement from above to ``~/.bashrc`` might work for ``bash`` users.

Then run:

.. code:: bash

   retesteth -t GeneralStateTests/stExample2 -- --filltests


``stExample2`` should be replaced with the name of the subdirectory you are working on.  ``--filltests`` option tells ``retesteth`` to fill tests. Final states are by default checked against the ``expect`` fields.

.. note::
   If your are working on an existing test directory, you can also use the ``--singletest <TESTNAME> --singlenet <FORKNAME>`` option which allows to select a specific test at specific fork. This prevents all files from the directory being modified (when using ``--filltests``). Furthermore ``-d <DATAINDEX> -g <GASINDEX> -v <VALUEINDEX>`` allow to select specific transaction from general state test.

``retesteth`` with ``--filltests`` fills every test filler it finds. The command might modify existing test cases. After running ``retesteth`` with ``--filltests`` , try running ``git status`` in the ``tests`` directory. If ``git status`` indicates changes in unexpected files, that is an indication that the behavior of ``Aleth`` changed unexpectedly.

.. note::
   If ``retesteth`` is looking for tests in the ``../../test/jsontests`` directory (falling back to a path relative to the ``Retesteth`` build directory if ``ETHEREUM_TEST_PATH`` is not set), you have probably not specified the ``--testpath`` option (use an absolute path if you do).


Trying the Filled Test
----------------------

Trying the Filled Test Locally
++++++++++++++++++++++++++++++

For trying the filled test, in ``retesteth/build`` directory, run the following (with ``ETHEREUM_TEST_PATH`` set):

.. code:: bash

   retesteth -t GeneralStateTests/stExample2


Trying the Filled Test in Travis CI
+++++++++++++++++++++++++++++++++++

The following instructions are highly specific to the Aleth C++ Ethereum client, which is currently used for test generation. Once a new test generation tool is ready, this process will likely change.

Goal here is the get the ``Aleth`` Travis CI build to run the new tests with ``Aleth`` to check they pass. To do that a PR has to be submitted to Aleth that updates the git submodule for ethereum/tests to point to a branch with the new tests.

Preparations on the ethereum/tests side
---------------------------------------

For trying the filled test(s) on ``Travis CI`` for ``Aleth``, the new test cases need to exist in a branch in ``ethereum/tests``. For this, ask somebody with a push permission to ``ethereum/tests``.


Preparations on the Aleth side
------------------------------

Enter ``aleth/test/jsontests`` directory, and checkout the new branch in ``ethereum/tests`` as described in the instructions above. Then go back to the main ``Aleth`` directory and perform ``git add test/jsontests`` followed by ``git commit``.

When you file this commit as a pull request to ``Aleth``, Travis CI should try the newly filled tests.

git commit
----------

After these are successful, the filler file and the filled test should be added to the ``tests`` repository. File these as a pull request.

If changes in the ``Aleth`` code itself were necessary, also file a pull request for these changes.

Advanced: Converting a GeneralStateTest Case into a BlockchainTest Case
=======================================================================

In the tests repository, each GeneralStateTest is eventually translated into a BlockchainTest.  This can be done by the following sequence of commands (remember ``ETHEREUM_TEST_PATH`` :-)).

.. code::

   retesteth -t GeneralStateTests/stExample2 -- --filltests --fillchain


followed by

.. code::

   retesteth -t GeneralStateTests/stExample2 -- --filltests


The second command is necessary because the first command modifies the GeneralStateTests in an undesired way.

After these two commands,


* ``git status`` to check if any GeneralStateTest has changed.  If yes, revert the changes, and follow section _\ ``Trying the Filled Test Locally``.  That will probably reveail an error that you need to debug.
* ``git add`` to add only the desired BlockchainTests.  Not all modified BlockchainTests are valuable because, when you run ``--fillchain`` twice, the two invocations always produce different BlockchainTests even there are no changes in the source.

Advanced: Retesteth selectors
==========================================


.. note::
   For generating blockchain tests version ``currentNumber`` must be equal to "1" and ``timestamp`` to "1000".


``retesteth`` has options to run tests selectively:


* ``--singletest callcall_00`` runs only one test of the name ``callcall_00``.
* ``--singlenet EIP150`` runs tests only using one version of the protocol.
* ``-d 0`` runs tests only on the first element in the ``data`` array of GeneralStateTest.
* ``-g 0`` runs tests only on the first element in the ``gas`` array of GeneralStateTest.
* ``-v 0`` runs tests only on the first element in the ``value`` array of GeneralStateTest.

``--singletest`` option removes skipped tests from the final test file, when ``retesteth`` is filling a BlockchainTest.

