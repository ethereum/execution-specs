.. _t8ntool_ref:

###########################################
Transition Tool
###########################################



Command Line Parameters
=======================
The command line parameters are used to specify the parameters, input files, and
output files.

Test Parameters
---------------
- **-\\-state.fork** *fork name*
- **-\\-state.reward** *block mining reward* (appears only in Block tests)
- **-\\-trace** produce a trace

Input Files
-----------
- **-\\-input.alloc** *full path to pretest allocation file*
- **-\\-input.txs** *full path to transaction file*
- **-\\-input.env** *full path to environment file*

.. note::

   If you want to specify any of this information in `stdin`, either 
   omit the parameter or use the value **stdin**.

Output Files
------------
- **-\\-output.basedir** *directory to write the output files*
- **-\\-output.result** *file name for test output*
- **-\\-output.alloc**  *file name for post test allocation file*
- **-\\-output.body** *file name for a list of rlp transactions* (a binary file)

.. note::

   If you want to receive this information into `stdout`, either omit
   the parameter or use the value **stdout**.


File Structures
===============
All of the transition tool files are in JSON format. Any values that are not
provided are assumed to be zero or empty, as applicable.


Transaction File
----------------
The transaction file is a list that contains maps, one for each transaction. 
This is an input to the tool, which `retesteth` calls `txs.json`. 

Every transaction can include these fields:

* `gas`
* `gasPrice`
* `input`, the transaction data
* `nonce`
* `value`, the value in WEI sent by the transaction
* `to`, the destination. If it is not specified the transaction creates a contract

In addition, there are a few special fields that may or may not appear, as explained
below.

Transaction Signatures
^^^^^^^^^^^^^^^^^^^^^^
Transactions can be previously signed by the caller that runs the tool. In that case
the transaction includes the `v`, `r`, and `s` values of the signature.

Alternatively, the transaction can include `secretKey`, in which the tool is responsible
for the signature.


EIP 2930
^^^^^^^^
`This EIP <https://eips.ethereum.org/EIPS/eip-2930>`_ defines a new transaction type
which includes a list of addresses and storage locations. If a transaction uses
EIP 2930 it would have two additional fields:

* `type` equal to one. If the transaction is normal it either has a value of zero 
  or does not appear at all. 
* `accessList`, an EIP 2930 access list.


Example 
^^^^^^^ 
The first transaction in this list is a normal transaction, already signed. 
The second is an EIP 2930 transaction which needs to be signed.

::

   [
      {
         "gas": "0x5208",
         "gasPrice": "0x2",
         "hash": "0x0557bacce3375c98d806609b8d5043072f0b6a8bae45ae5a67a00d3a1a18d673",
         "input": "0x",
         "nonce": "0x0",
         "r": "0x9500e8ba27d3c33ca7764e107410f44cbd8c19794bde214d694683a7aa998cdb",
         "s": "0x7235ae07e4bd6e0206d102b1f8979d6adab280466b6a82d2208ee08951f1f600",
         "to": "0x8a8eafb1cf62bfbeb1741769dae1a9dd47996192",
         "v": "0x1b",
         "value": "0x1"
      },
      {
         "gas": "0x4ef00",
         "gasPrice": "0x1",
         "chainId": "0x1",
         "input": "0x",
         "nonce": "0x0",
         "to": "0x000000000000000000000000000000000000aaaa",
         "value": "0x1",
         "type" : "0x1",
         "accessList": [
            {
               "address": "0x0000000000000000000000000000000000000aaaa",
               "storageKeys": [
                  "0x0000000000000000000000000000000000000000000000000000000000000000",
                  "0x0000000000000000000000000000000000000000000000000000000000000012"
               ]
            },
            {
               "address": "0x0000000000000000000000000000000000000aaab",
               "storageKeys": [
                  "0x00000000000000000000000000000000000000000000000000000000000060A7",
                  "0x0000000000000000000000000000000000000000000000000000000000000012"
               ]
            }
         ]
         "v": "0x0",
         "r": "0x0",
         "s": "0x0",
         "secretKey": "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
      }
   ]


Environment File
----------------
This file is a map with the execution environment. 
This is an input to the tool, which `retesteth` calls `env.json`.
It has these fields:


* `currentCoinbase`
* `currentDifficulty`
* `currentGasLimit`
* `currentNumber`
* `currentTimestamp`
* `previousHash`, the hash of the previous (`currentNumber`-1) block
* `blockHashes`, a map of historical block numbers and their hashes

.. note::

   Some tests include multiple blocks. In that case, the test software runs 
   `t8ntool` multiple times, one per block. 


Example
^^^^^^^

::

  {
     "currentCoinbase" : "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
     "currentDifficulty" : "0x020000",
     "currentGasLimit" : "0x05f5e100",
     "currentNumber" : "0x01",
     "currentTimestamp" : "0x03e8",
     "previousHash" : "0xe729de3fec21e30bea3d56adb01ed14bc107273c2775f9355afb10f594a10d9e",
     "blockHashes" : {
         "0" : "0xe729de3fec21e30bea3d56adb01ed14bc107273c2775f9355afb10f594a10d9e"
     }
  }


Allocation Files
----------------
These files show the state of various accounts and contracts on the blockchain.
In `retesteth` there are two of these files:
`alloc.json` which is the input state and `outAlloc.json`
which is the output state.

The file is a map of `address` values to account information. The account 
information that can be provided is:

* `balance` 
* `code` (in machine language format)
* `nonce`
* `storage`

Example
^^^^^^^

::

   {
       "a94f5374fce5edbc8e2a8697c15331677e6ebf0b": {
           "balance": "0x5ffd4878be161d74",
           "code": "0x5854505854",
           "nonce": "0xac",
           "storage": {
              "0x0000000000000000000000000000000000000000000000000000000000000000": 
              "0x0000000000000000000000000000000000000000000000000000000000000004"
           }
        },
        "0x8a8eafb1cf62bfbeb1741769dae1a9dd47996192":{
           "balance": "0xfeedbead",
           "nonce" : "0x00"
        }
   }






Result File
-----------
In `retesteth` this file is called `out.json`. It is the post state after 
processing the block. It should include the following fields:

* `stateRoot`
* `txRoot`
* `receiptRoot`
* `logsHash`
* `logsBloom`, the `bloom filter <https://en.wikipedia.org/wiki/Bloom_filter>`_ for
  the logs.
* `receipts`, a list of maps, one for each transaction, with the transaction receipt.
  Each of those receipts includes these fields:

  * `root`
  * `status`
  * `cumulativeGasUsed`
  * `logsBloom`
  * `logs`
  * `transactionHash`
  * `contractAddress`, the address of the created contract, if any
  * `gasUsed`
  * `blockHash`, all zeros because this is created before the block is finished
  * `transactionIndex`


Example
^^^^^^^

::

   {
     "stateRoot": "0x1c99b01120e7a2fa1301b3505f20100e72362e5ac3f96854420e56ba8984d716",
     "txRoot": "0xb5eee60b45801179cbde3781b9a5dee9b3111554618c9cda3d6f7e351fd41e0b",
     "receiptRoot": "0x86ceb80cb6bef8fe4ac0f1c99409f67cb2554c4432f374e399b94884eb3e6562",
     "logsHash": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
     "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
     "receipts": [
        {
            "root": "0x",
            "status": "0x1",
            "cumulativeGasUsed": "0xa878",
            "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            "logs": null,
            "transactionHash": "0x4e6549e2276d1bc256b2a56ead2d9705a51a8bf54e3775fbd2e98c91fb0e4494",
            "contractAddress": "0x0000000000000000000000000000000000000000",
            "gasUsed": "0xa878",
            "blockHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "transactionIndex": "0x0"
        }
     ]
   }



Trace Files
-----------
If **-\\-trace** is specified, the t8ntool creates a file (or files) called 
`trace-<transaction number>-<transaction hash>.jsonl`. The format of this file
is specified in 
`EIP 3155 <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-3155.md>`_.

If the transaction fails and does not produce a hash, the name of the file is
still `trace-<transaction number>-<value that is a legitimate hash>.jsonl`.



Using Standard Input and Output
===============================
It should also be possible to run a `t8ntool` with input coming from `stdin`
and output going to `stdout`. In this case, the input is all one object and
the output is all one object.


Input
-----
When the input is provided using `stdin`, it can have any combination 
of these three fields (whichever ones aren't provided in file form)

* `txs`, a list of transactions
* `alloc`, a map of the pretest accounts
* `env`, a map of the execution environment


Output
------
When the output goes to `stdout`, it can have any combination of these fields
(whichever ones don't have a specified output file):

* `result`, the poststage
* `body`, the transactions and their results 

