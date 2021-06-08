.. _internals_tutorial:

###########################################
Test Internals
###########################################
`Ori Pomerantz <mailto://qbzzt1@gmail.com>`_

In this tutorial you learn more about the internal representation of Ethereum
tests and how to run them with additional details. In theory you could write 
any test you want without understanding these details, but they are useful
for debugging.


Compiled Tests
=================
By default the compiled version of 
**tests/src/<test type>Filler/<directory>/<test>Filler** goes in
**tests/<test type>/<directory><test>.json**. For example, after we copy
**tests/doc/tutorial_samples/01_add22.yml** to 
**tests/src/GeneralStateTests/stExample/01_add22.yml** and compile it,
it is available at 
**tests/GeneralStateTests/stExample/01_add22.json**. Here it is with 
explanations:

::

  {
    "01_add22" : {

The **_info:** section includes any comments you put in the source code of the 
test, as well as information about the files used to generate the test 
(the test source code, the evm compiler if any, the client software used 
to fill in the data, and the tool that actually compiled the test).

::

        "_info" : {
            "comment" : "You can put a comment here",
            "filling-rpc-server" : "Geth-1.9.20-unstable-54add425-20200814",
            "filling-tool-version" : "retesteth-0.0.8-docker+commit.96775cc7.Linux.g++",
            "lllcversion" : "Version: 0.5.14-develop.2020.8.15+commit.9189ad7a.Linux.g++",
            "source" : "src/GeneralStateTestsFiller/stExample/01_add22Filler.yml",
            "sourceHash" : "6b5a88627d0b69c7f61fb05f35ac3f14066d2f4bbe248aa08c3091d7534744d8"            
        },
  
The **env:** and **transaction:** sections contain the information provided 
in the source code. 
  
::        
        
        "env" : {
            ...
            },
        "transaction" : {
            ...
            },

The **pre:** section contains mostly information from the source file,
but any code provided source (either LLL or Solidity) is compiled.

::

        "pre" : {
            "0x095e7baea6a6c7c4c2dfeb977efac326af552d87" : {
                "balance" : "0x0ba1a9ce0ba1a9ce",
                "code" : "0x600260020160005500",
                "nonce" : "0x00",
                "storage" : {
                }
            },
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b" : {
               ...
            }
        },


The **post:** section is the situation after the test is run. This could be different for 
`different versions of the Ethereum protocol 
<https://en.wikipedia.org/wiki/Ethereum#Milestones>`_, 
so there is a value for every version that was checked. In this case, the 
only one is Istanbul.

::        

        "post" : {
            "Istanbul" : [
                {
                    "indexes" : {
                        "data" : 0,
                        "gas" : 0,
                        "value" : 0
                    },
                    
Instead of keeping the entire content of the storage and logs that are expected, 
it is enough to just store hashes of them. 
                    
::

                    "hash" : "0x884b8640efb63506c2f8c2d9514335b678815e1ed362107628cf1cd6edd658c2",
                    "logs" : "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
                }
            ]
        }
  }
  

Virtual Machine Trace
=====================
If you are using the geth t8ntool, can use the **\\-\\-vmtrace** command line option 
to get a trace of the virtual machine. For example, this is the command to 
get a trace of **01_add22**:

::

    ./dretesteth.sh -t GeneralStateTests/stExample -- --singletest 01_add22 \
       --testpath ~/tests --datadir /tests/config --filltests --vmtrace



Normal Virtual Machine Trace
--------------------------------
This is the trace produced by the command above:

::


   VMTrace: (stExample/01_add22, fork: Berlin, TrInfo: d: 0, g: 0, v: 0)
   Transaction number: 0, hash: 0x4e6549e2276d1bc256b2a56ead2d9705a51a8bf54e3775fbd2e98c91fb0e4494

   N    OPNAME   GASCOST  TOTALGAS REMAINGAS               ERROR
   0     PUSH1         3         0  79978984                    
   1     PUSH1         3         3  79978981                    
   2       ADD         3         6  79978978                    
   3     PUSH1         3         9  79978975                    
   4    SSTORE     20000        12  79978972                    
         SSTORE [0x0] = 0x4
   5      STOP         0     20012  79958972                    

   {"stateRoot":"0x54d60243629f67e60925f5a9d6daf5f5ee3d774a728aa10c4ef05b8b20b1e192"}





Raw Virtual Machine Trace
--------------------------
The virtual machine trace above does not include the value of the 
program counter (PC), the content of the stack, or the full content of the 
storage and memory for the account. To get this information
you need the raw trace:


::

    ./dretesteth.sh -t GeneralStateTests/stExample -- --singletest 01_add22 \
       --testpath ~/tests --datadir /tests/config --filltests --vmtraceraw | more




The program creates this trace:

::

   VMTrace: (stExample/01_add22, fork: Istanbul, TrInfo: d: 0, g: 0, v: 0)
   Transaction number: 0, hash: 0x4e6549e2276d1bc256b2a56ead2d9705a51a8bf54e3775fbd2e98c91fb0e4494

This is the status before the first operation. For the sake of clarity I passed it
through a `JSON formatter <https://jsonformatter.curiousconcept.com/>`_.

:: 

   {

The program counter starts at zero. The opcode at that point is 96, or in
hexadecimal **0x60**. Looking at `the opcode table 
<https://github.com/crytic/evm-opcodes>`_, this operation pushes a one byte
value on the stack.

::

     "pc":0,
     "op":96,

The amount of gas that is currently available, and the cost of this opcode

::

     "gas":"0x4c461e8",
     "gasCost":"0x3",

Current short term (not to be stored as part of the blockchain) values: RAM,
the computation stack, and the return locations stack.

::

     "memory":"0x",
     "memSize":0,
     "stack":[
      
     ],
     "returnStack":[
      
     ],
     "returnData":null,


The depth of the contract call. The contract called directly by the transaction is 
depth one. If that contract calls code in a different contract, that code will
run with depth two, etc.


::

     "depth":1,

`Contracts get a refund for releasing storage they no longer need by setting it to zero) 
<https://media.consensys.net/ethereum-gas-fuel-and-fees-3333e17fe1dc#:~:text=Gas%20refund>`_.
This is the amount of the refund.

::

     "refund":0,


The name of the opcode (corresponding to the **op** value above).

::

     "opName":"PUSH1",

The error, if any.

::

     "error":""
  }


The second operation is almost identical to the first. The differences are:

- The program counter is two, after running an opcode with two bytes (the
  opcode itself and the value being pushed)
- The gas counter is lower by three (the cost of the previous operation)
- The stack, rather than empty, has a single value: **0x2**.


::

   {"pc":2,"op":96,"gas":"0x4c461e5","gasCost":"0x3","memory":"0x","memSize":0,"stack":["0x2"],"returnStack":[],"returnData":null,"depth":1,"refund":0,"opName":"PUSH1","error":""}


Now the evm adds the two top values (turning a stack of **["0x2", "0x2"]** into
**["0x4"]**) and then pushes the value zero.

::

  {"pc":4,"op":1,"gas":"0x4c461e2","gasCost":"0x3","memory":"0x","memSize":0,"stack":["0x2","0x2"],"returnStack":[],"returnData":null,"depth":1,"refund":0,"opName":"ADD","error":""}
  {"pc":5,"op":96,"gas":"0x4c461df","gasCost":"0x3","memory":"0x","memSize":0,"stack":["0x4"],"returnStack":[],"returnData":null,"depth":1,"refund":0,"opName":"PUSH1","error":""}


Now we store the value at the second place in the stack at the location in the 
first place. This is writing to the state, so it is an expensive operation, costing
twenty thousand gas.

::

  {"pc":7,"op":85,"gas":"0x4c461dc","gasCost":"0x4e20","memory":"0x","memSize":0,"stack":["0x4","0x0"],"returnStack":[],"returnData":null,"depth":1,"refund":0,"opName":"SSTORE","error":""}


Finally, stop the evm. The final line gives the output return value, the amount of gas
used, and how long it took to run the program.

::

  {"pc":8,"op":0,"gas":"0x4c413bc","gasCost":"0x0","memory":"0x","memSize":0,"stack":[],"returnStack":[],"returnData":null,"depth":1,"refund":0,"opName":"STOP","error":""}
  {"output":"","gasUsed":"0x4e2c","time":527368}




  
  
Conclusion
==========
At this point you should be able to write and debug Ethereum tests. 
