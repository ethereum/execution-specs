.. _vm_tests:


=================================
Generated Virtual Machine Tests
=================================

Location `/BlockChainTests/ValidBlocks/VMTests 
<https://github.com/ethereum/tests/tree/develop/BlockChainTests/ValidBlocks/VMTests>`_


The VM tests aim is to test the basic workings of the VM in
isolation.

This is specifically not meant to cover transaction, creation or call 
processing, or management of the state trie. Indeed at least one implementation 
tests the VM without calling into any Trie code at all.

A VM test is based around the notion of executing a single piece of code as part of a transaction, 
described by the ``exec`` portion of the test. The overarching environment in which it is 
executed is described by the ``env`` portion of the test and includes attributes 
of the current and previous blocks. A set of pre-existing accounts are detailed 
in the ``pre`` portion and form the world state prior to execution. Similarly, a set 
of accounts are detailed in the ``post`` portion to specify the end world state.

The gas remaining (``gas``), the log entries (``logs``) as well as any output returned 
from the code (``out``) is also detailed.


Test Implementation
===================

It is generally expected that the test implementer will read ``env``, ``exec`` and ``pre`` 
then check their results against ``gas``, ``logs``, ``out``, ``post`` and ``callcreates``. 
If an exception is expected, then latter sections are absent in the test. Since the 
reverting of the state is not part of the VM tests.

Because the data of the blockchain is not given, the opcode BLOCKHASH could not 
return the hashes of the corresponding blocks. Therefore we define the hash of 
block number n to be SHA3-256("n").

Since these tests are meant only as a basic test of VM operation, the ``CALL`` and 
``CREATE`` instructions are not actually executed. To provide the possibility of 
testing to guarantee they were actually run at all, a separate portion ``callcreates`` 
details each ``CALL`` or ``CREATE`` operation in the order they would have been executed. 
Furthermore, gas required is simply that of the VM execution: the gas cost for 
transaction processing is excluded.

Test Structure
==============

::

	{
	   "test name 1": {
	       "_info" : { ... },
		   "env": { ... },
		   "pre": { ... },
		   "exec": { ... },
		   "gas": { ... },
		   "logs": { ... },
		   "out": { ... },
		   "post": { ... },
		   "callcreates": { ... }
	   },
	   "test name 2": {
   	       "_info" : { ... },
		   "env": { ... },
		   "pre": { ... },
		   "exec": { ... },
		   "gas": { ... },
		   "logs": { ... },
		   "out": { ... },
		   "post": { ... },
		   "callcreates": { ... }
	   },
	   ...
	}

.. _info_vmtests:
.. include:: ../test_types/TestStructures/info.rst
.. _env_vmtests:
.. include:: ../test_types/TestStructures/GeneralStateTests/env.rst
.. _pre_vmtests:
.. include:: ../test_types/TestStructures/pre.rst

Exec Section
============

::

    {
        "exec" : {
            "address" : "0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
            "caller" : "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "code" : "0x600260021660005500",
            "data" : "0x",
            "gas" : "0x0186a0",
            "gasPrice" : "0x0c",
            "origin" : "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "value" : "0x0b"
        },
    }


**Fields**

============= ============== =============================================================================
``address``   **FH20**       The address of the account under which the code is executing, to be returned by the ``ADDRESS`` instruction.
``origin``    **FH20**       The address of the execution's origin, to be returned by the ``ORIGIN`` instruction.
``caller``    **FH20**       The address of the execution's caller, to be returned by the ``CALLER`` instruction.
``value``     **VALUE**      The value of the call (or the endowment of the create), to be returned by the ``CALLVALUE`` instruction.
``data``      **BYTES**      The input data passed to the execution, as used by the ``CALLDATA``... instructions. Given as an array of byte values. See $DATA_ARRAY.
``code``      **BYTES**      The actual code that should be executed on the VM (not the one stored in the state(address)) . See $DATA_ARRAY.
``gasPrice``  **VALUE**      The price of gas for the transaction, as used by the ``GASPRICE`` instruction.
``gas``       **VALUE**      The total amount of gas available for the execution, as would be returned by the ``GAS`` instruction were it be executed first.
============= ============== =============================================================================

.. include:: types.rst

Post Section
============

Same as Pre/preState Section


Callcreates Section
===================

The ``callcreates`` section details each ``CALL`` or ``CREATE`` instruction that has been executed. It is an array of maps with keys:

* ``data``: An array of bytes specifying the data with which the ``CALL`` or ``CREATE`` operation was made. In the case of ``CREATE``, this would be the (initialisation) code. See $DATA_ARRAY.
* ``destination``: The receipt address to which the ``CALL`` was made, or the null address (``"0000..."``) if the corresponding operation was ``CREATE``.
* ``gasLimit``: The amount of gas with which the operation was made.
* ``value``: The value or endowment with which the operation was made.

Logs Section
============

The ``logs`` sections contains the hex encoded hash of the rlp encoded log entries, reducing the overall size of the test files while still verifying that all of the data is accurate (at the cost of being able to read what the data should be).
Each logentry has the format:

keccak(rlp.encode(log_entries))

(see https://github.com/ethereum/py-evm/blob/7a96fa3a2b00af9bea189444d88a3cce6a6be05f/eth/tools/_utils/hashing.py#L8-L16)

The gas and output Keys
=======================

Finally, there are two simple keys, ``gas`` and ``out``:

* ``gas``: The amount of gas remaining after execution.
* ``out``: The data, given as an array of bytes, returned from the execution (using the ``RETURN`` instruction). See $DATA_ARRAY.

 **$DATA_ARRAY** - type that intended to contain raw byte data   
  and for convenient of the users is populated with three   
  types of numbers, all of them should be converted and   
  concatenated to a byte array for VM execution.   

* The types are:    
  1. number - (unsigned 64bit)
  2. "longnumber" - (any long number)
  3. "0xhex_num"  - (hex format number)


   e.g: ``````[1, 2, 10000, "0xabc345dFF", "199999999999999999999999999999999999999"]``````			 
