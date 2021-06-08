.. state_transition_tutorial:

###########################################
State Transition Tests
###########################################

`Ori Pomerantz <mailto://qbzzt1@gmail.com>`_

In this tutorial you learn how to write and execute Ethereum state transition 
tests. These tests can be very simple, for example testing a single evm assembler 
opcode, so this is a good place to get started. This tutorial is not 
intended as a comprehensive reference, look in the table of content on the left.

The Environment
===============
Before you start, make sure you read and understand the `Retesteth Tutorial
<retesteth-tutorial.html>`_, and create the docker environment explained there.


Compiling Your First Test
=========================
Before we get into how tests are built, lets compile and run a simple one.

#. The source code of the tests is in **tests/src**. It is complicated to 
   add another tests directory, so we will use
   **GeneralStateTestsFiller/stExample**.
   
   ::

      cd ~/tests/src/GeneralStateTestsFiller/stExample
      cp ~/tests/docs/tutorial_samples/01* .
      cd ~
  
#. The source code of tests doesn't include all the information required 
   for the test. Instead, you run **retesteth.sh**,
   and it runs a client with the Ethereum Virtual Machine (evm) to fill in the 
   values. This creates a compiled
   version in **tests/GeneralStateTests/stExample**.

   ::

      ./dretesteth.sh -t GeneralStateTests/stExample -- \
          --singletest 01_add22 --testpath ~/tests \
          --datadir /tests/config --filltests
      sudo chown $USER tests/GeneralStateTests/stExample/*

#. Run the test normally, with verbose output:

   ::

      ./dretesteth.sh -t GeneralStateTests/stExample -- \
         --singletest 01_add22 --testpath ~/tests \
         --datadir /tests/config --clients geth --verbosity 5

The Source Code
---------------
Now that we've seen that the test works, let's go through it line by line. 
This test specification is written in YAML, if you are not familiar 
with this format `click here <https://www.tutorialspoint.com/yaml/index.htm>`_. 

All the fields are defined under the name of the test. Note that YAML comments 
start with a hash (**#**) and continue to the end of the line.

If you want to follow along with the full source code
You can see the complete code, `here 
<https://github.com/ethereum/tests/blob/develop/docs/tutorial_samples/01_add22Filler.yml>`_

::

  # The name of the test
  01_add22:

This is the general Ethereum environment before the transaction:

::

  env:
      currentCoinbase: 2adc25665018aa1fe0e6bc666dac8fc2697ff9ba
      currentDifficulty: '0x20000'
      currentGasLimit: "100000000"
      currentNumber: "1"
      currentTimestamp: "1000"
      previousHash: 5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6


This is where you put human readable information. In contrast to ``#`` comments, 
these comment fields get copied to the compiled JSON file for the test.

::

    _info:
      comment: "You can put a comment here"
  
These are the relevant addresses and their initial states before the test starts:
  
::      

    pre:


This is a contract address. As such it has code, which can be in one of three formats:

#. Ethereum virtual machine (EVM) machine language 
#. `Lisp Like Language (lll) <http://blog.syrinx.net/the-resurrection-of-lll-part-1/>`_. 
   One
   advantage of lll is that `it lets us use Ethereum Assembler almost directly
   <https://lll-docs.readthedocs.io/en/latest/lll_reference.html#evm-opcodes>`_.
#. `Solidity <https://cryptozombies.io/>`_, which is the standard language for 
   Ethereum contracts. Solidity is well known, but it is not ideal for VM tests 
   because it adds its own code to compiled contracts.
   
::

   095e7baea6a6c7c4c2dfeb977efac326af552d87:
     balance: '0x0ba1a9ce0ba1a9ce'

LLL code can be very low level. In this case, **(ADD 2 2)** is translated 
into three opcodes:

* PUSH 2
* PUSH 2
* ADD (which pops the last two values in the stack, adds them, 
  and pushes the sum into the stack).

This expression **[[0]]** is short hand for **(SSTORE 0 <the value at the top of the 
stack>)**. It stores the value (in this case, four) in location 0. 

::        
        
     code: |
       {
         ; Add 2+2
         [[0]] (ADD 2 2)
       }
       nonce: '0'

Every address in Ethereum has associated storage,
which is essentially a lookup table. `You can read more about it here 
<https://applicature.com/blog/blockchain-technology/ethereum-smart-contract-storage>`_.
In this case the storage is initially empty.

::

        storage: {}

This is a "user" address. As such, it does not have code. Note that you still 
have to specify the storage.

::

      a94f5374fce5edbc8e2a8697c15331677e6ebf0b:
        balance: '0x0ba1a9ce0ba1a9ce'
        code: '0x'
        nonce: '0'
        storage: {}

This is the transaction that will be executed to check the code.
There are several scalar fields here:

* **gasPrice** is the price of gas in Wei.
* **nonce** has to be the same value as the user address
* **to** is the contract we are testing. If you want to create a contract, keep the 
  **to** definition, but leave it empty.

Additionally, these are several fields that are lists of values. The reason to
have lists instead of a single value is to be able to run multiple similar
tests from the same file (see the **Multitest Files** section below).

* **data** is the data we send
* **gasLimit** is the gas limit
* **value** is the amount of Wei we send with the transaction

::

    transaction:
      data:
      - '0x10'
      gasLimit:
      - '80000000'
      gasPrice: '1'
      nonce: '0'
      to: 095e7baea6a6c7c4c2dfeb977efac326af552d87
      value:
      - '1'

This is the state we expect after running the transaction on the **pre** state.
The **indexes:** subsection is used for multitest files, for now just copy and
paste it into your tests.

::

   expect:
      - indexes:
          data: !!int -1
          gas:  !!int -1
          value: !!int -1
        network:
          - '>=Istanbul'

We expect the contract's storage to have the result, in this case 4.

::          
          
        result:
          095e7baea6a6c7c4c2dfeb977efac326af552d87:
            storage:
              0x00: 0x04

Failing a Test
--------------
To verify that **retesteth** really does run tests, lets fail one. 
The `**02_fail**
<https://github.com/ethereum/tests/blob/develop/docs/tutorial_samples/02_failFiller.yml>`_ 
test is almost identical to **01_add22**, except that it expects 
to see that 2+2=5. Here are the steps to use it.

#. Copy the test to the `stExample` directory: 
   
   ::

      cp ~/tests/docs/tutorial_samples/02* ~/tests/src/GeneralStateTestsFiller/stExample

#. Fill the information and run the test:

   ::

      ./dretesteth.sh -t GeneralStateTests/stExample -- \
         --singletest 02_fail --testpath ~/tests \
         --datadir /tests/config --filltests

#. Delete the test so we won't see the failure when we run future tests
   (you can run all the tests in a directory by omitting the 
   **--singletest** parameter:

   ::
 
      rm ~/tests/src/GeneralStateTestsFiller/stExample/02_*



Yul Tests
=========
`Yul <https://docs.soliditylang.org/en/v0.8.3/yul.html>`_ is a language that is very
close to EVM assembler. As such it is a good language for writing tests. You can see 
a Yul test at `tests/docs/tutorial_samples/09_yulFiller.yml 
<https://github.com/ethereum/tests/blob/develop/docs/tutorial_samples/09_yulFiller.yml>`_.

This is a sample contract:

::

    cccccccccccccccccccccccccccccccccccccccc:
      balance: '0x0ba1a9ce0ba1a9ce'
      code: |
       :yul {
         let cellAddr := sub(10,10)

         sstore(cellAddr,add(60,9))
       }
      nonce: 1
      storage: {}


It is very similar to an LLL test, except for having the **:yul** keyword before the
opening curly bracket (**{**).


  
Solidity Tests
==============
You can see a solidity test at `tests/docs/tutorial_samples/03_solidityFiller.yml 
<https://github.com/ethereum/tests/blob/develop/docs/tutorial_samples/03_solidityFiller.yml>`_.
Here are the sections that are new.

.. note::

   The Solidity compiler adds a lot of extra code that handles ABI encoding,
   ABI decoding, contract constructors, etc. This makes tracing and debugging a lot 
   harder, which makes Solidity a bad choice for most Ethereum client tests.

   This feature is available for tests where it is useful, but LLL or Yul is
   usually a better choice.



You can have a separate **solidity:** section for your code. This is useful 
because Solidity code tends to be longer than LLL (or Yul) code.

::

  solidity: |
      // SPDX-License-Identifier: GPL-3.0
      pragma solidity >=0.4.16 <0.8.0;
      contract Test {

`Solidity keeps state variables in the storage 
<https://solidity.readthedocs.io/en/v0.7.0/internals/layout_in_storage.html>`_, 
starting with location 0. We can use state variables for the results of 
operations, and check them in the **expect:** section

::

        uint256 storageVar = 0xff00ff00ff00ff00;
        function val2Storage(uint256 addr, uint256 val) public
        {
          storageVar = val;

Another possibility is to use the SSTORE opcode directly to write to storage. 
`This is the format to embed assembly into Solidity 
<https://solidity.readthedocs.io/en/v0.7.0/assembly.html>`_.

::

          assembly { sstore(addr, val) }
        }   // function val2Storage
      }     // contract Test
      
To specify a contract's code you can use **:solidity <name of contract>**. 
Alternatively, you can put the solidity code directly in the account's 
**code:** section if it has **pragma solidity**
(otherwise it is compiled as LLL).

::

  pre:
    cccccccccccccccccccccccccccccccccccccccc:
      balance: '0x0ba1a9ce0ba1a9ce'
      code: ':solidity Test'
      nonce: '0'
      storage: {}
      
    
In contrast to LLL, Solidity handles function signatures and parameters for you. 
Therefore, the transaction data has to conform to the 
`Application Binary Interface (ABI) 
<https://solidity.readthedocs.io/en/v0.7.0/abi-spec.html>`_. You do not have to calculate the 
data on your own, just start it with **:abi** followed by the `function signature 
<https://medium.com/@piyopiyo/how-to-get-ethereum-encoded-function-signatures-1449e171c840>`_
and then the parameters. These parameters can be bool, uint, single dimension arrays, and strings.

.. note::
   ABI support is a new feature, and may be buggy. Please report any bugs you
   encounter in this feature.

    
::

  transaction:
    data:
    - :abi val2Storage(uint256,uint256) 5 69
    gasLimit:
    - '80000000'
    
    
The other sections of the test are exactly the same as they are in an LLL test. 

ABI values
----------
These are examples of the values that **:abi** can have.

* **:abi baz(uint32,bool) 69 1**: Call **baz** with a 32 bit value (69) 
  and a true boolean value

* **:abi bar(bytes3[2]) ["abc", "def"]**: Call **bar** with a two value array, 
  each value three bytes

* **:abi sam(bytes,bool,uint256[]) "dave" 0 [1,2,3]**: Call **sam** with a string 
  ("dave"), a false boolean value, and an array of three 256 bit numbers.

* **:abi f(uint256,uint32[],bytes10,bytes) 0x123 [0x456, 0x789] "1234567890" "Hello, world"**: 
  Call **f** with these parameters

  * An unsigned 256 bit integer
  
  * An array of 32 bit values (it can be any size)
  
  * A string of ten bytes 
  
  * A string which could be any size

* **:abi g(uint256[][],string[]) [[1,2],[3],[4,5] ["one","two","three"]**: 
  Call **g** with two parameters, a two dimensional array of uint256 values and
  an array of strings.


* **:abi h(uint256,uint32[],bytes10,bytes) 291 [1110,1929] "1234567890"** 
  **"Hello, world!"**: Call **h** with a uint256, an array of uint32 values of
  unspecified size, ten bytes, and a parameter with an unspecified number of bytes. 
  

* **:abi ff(uint256,address) 324124 "0xcd2a3d9f938e13cd947ec05abc7fe734df8dd826"**:
  Call **ff** with a uint256 and an address (Ethererum addresses are twenty bytes).


  

Multitest Files
===============
It is possible to combine multiple similar tests in one file. `Here is an example 
<https://github.com/ethereum/tests/blob/develop/docs/tutorial_samples/04_multitestFiller.yml>`_.

There are two steps to doing that:

- Modify the **transaction:** section. This section has three subsections that are 
  lists. You can add multiple values to the **data:**, **gasLimit:**, and 
  **value:**. 

  For example:

  ::

    transaction:
       data:
       - :abi val2Storage(uint256,uint256) 0x10 0x10
       - :abi val2Storage(uint256,uint256) 0x11 0x11
       - :abi val2Storage(uint256,uint256) 0x11 0x12
       - :abi val2Storage(uint256,uint256) 0x11 0x11
       gasLimit:
       - '80000000'
       gasPrice: '1'
       nonce: '0'
       to: cccccccccccccccccccccccccccccccccccccccc
       secretKey: "45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
       value:
       - 0

- The **expect:** section is also a list, and can have multiple values. Just put the
  indexes to the correct **data**, **gas**, and **value** values, and have the correct
  response in the **result:** section.

  For example:

  :: 

     expect:

  The indexes are integer values. By default YAML values are strings. 
  The **!!int** overrides this. These are all the first values in their lists,
  so the data is equivalent to the call **val2Storage(0x10, 0x10)**.

  ::

       - indexes:
           data: !!int 0
           gas:  !!int 0
           value: !!int 0
         network:
           - '>=Istanbul'
         result:
           cccccccccccccccccccccccccccccccccccccccc:
             storage:
               0:    0x10
               0x10: 0x10

  This is for the second and fourth items in the **data:** subsection above. 
  When you have multiple values
  that produce the same test results, you can specify **data**, **gas**, or **value**
  as a list instead of a single index.

  ::

       - indexes:
           data: 
           - !!int 1
           - !!int 3
           gas:  !!int 0
           value: !!int 0
         network:
           - '>=Istanbul'
         result:
           cccccccccccccccccccccccccccccccccccccccc:
             storage:
               0:    0x11
               0x11: 0x11

Multiple Tests, Same Result
---------------------------
When you have multiple tests that produce the same results,
you do not have to list them individually in the **expect:**
section.

**Range**. You can specify a range, such as **4-6**, inside
the **expect.data:** list. Remember *not* to specify !!int, the range
is a string, not an integer.

**Label**. You can preface the value with **:label <word> <value>**:

::

    transaction:
      data:
      - :label odd  :abi f(uint) 1
      - :label even :abi f(uint) 2
      - :label odd  :abi f(uint) 3
      - :label even :abi f(uint) 4
      - :label odd  :abi f(uint) 5
      - :label even :abi f(uint) 6
      - :label odd  :abi f(uint) 7
      - :label even :abi f(uint) 8
   
In the **expect.data:** list, you specify **:label <word>** and it applies
to every value that has that label.

::

    expect:
      - indexes:
          data:
          - :label odd
          - :label even
          gas: !!int -1
          value: !!int -1
         


Conclusion
==========
At this point you should be able to run simple tests that verify the EVM opcodes work 
as well as more complex algorithms work as expected. You are, however, limited to
a single transaction in a single block. In a next tutorial, *Blockchain Tests*, 
you will learn how to write blockchain tests that can involve multiple blocks, 
each of which can have multiple transactions.
