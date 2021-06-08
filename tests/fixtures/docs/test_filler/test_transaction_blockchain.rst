Transaction
=============

This is the data of a transaction. Every block contains a list of transactions


Format
------------


.. list-table::
   :header-rows: 1

   * - JSON

     - YAML

   * -

       ::

           {
               "name-of-test":
               { 
                  <other sections>
                  "blocks": [
                     { 
                       transactions: [
                         {
                           data: "0xDA7A",
                           gasLimit: "0x6a506a50",
                           gasPrice: 1,
                           value: 1,
                           to: "add13ess01233210add13ess01233210",
                           secretKey: "5ec13e7 ... 5ec13e7"
                           nonce: '0x909ce'
                         },
                         {
                           data: "0xDA7A",
                           accessList: [
                             {  
                                "address": "0xcccccccccccccccccccccccccccccccccccccccd",
                                "storageKeys": ["0x1000", "0x60A7"]
                             },
                             {  
                                "address": "0xccccccccccccccccccccccccccccccccccccccce",
                                "storageKeys": []
                             }
                           ], 
                           gasLimit: "0x6a506a50",
                           maxFeePerGas: 1000,
                           maxPriorityFeePerGas: 10,
                           value: 1,
                           to: "add13ess01233210add13ess01233210",
                           secretKey: "5ec13e7 ... 5ec13e7"
                           nonce: '0x909ce'
                         },
                         <other transactions>
                       ]
                       <other block fields>
                     },
                     <other blocks>
                  ]
              }


     - ::

           <test-name>:
             <other sections>
             blocks:
             - transactions:
               - data: 0xDA7A
                 gasLimit: '0x6a506a50'
                 maxFeePerGas: 1000
                 maxPriorityFeePerGas: 10
                 value: 1
                 to: "add13ess01233210add13ess01233210"
                 secretKey: "5ec13e7 ... 5ec13e7"
                 nonce: '0x909ce'
               - data: 0xDA7A
                 accessList: 
                 - address: 0xcccccccccccccccccccccccccccccccccccccccd
                   storageKeys:
                   - 0x1000
                 - address: 0xcccccccccccccccccccccccccccccccccccccccc
                   storageKeys: []
                 gasLimit: '0x6a506a50'
                 gasPrice: "1"
                 value: 1
                 to: "add13ess01233210add13ess01233210"
                 secretKey: "5ec13e7 ... 5ec13e7"
                 nonce: '0x909ce'
               - <another transaction>
               <other block fields>
             - <another block>


Fields
--------------
- **data**:

  The data, either in hexadecimal or an 
  `ABI call <https://solidity.readthedocs.io/en/v0.7.1/abi-spec.html>`_
  with this format:
  **:abi <function signature> <function parameters separated by spaces>**.


- **accessList**:

  An optional `EIP2930 <https://eips.ethereum.org/EIPS/eip-2930>`_ access list. 
  The **accessList** is a list of structures, each of which has to have an **address**
  and a list of **storageKeys** (which may be empty).


- **gasLimit**:
  
  Gas limit for the transaction


- **gasPrice**:

  Gas price in Wei, prior to London (changed by `EIP 1559 <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1559.md>`_).

- **maxFeePerGas**:

  Maximum acceptable gas price in Wei. Available in London and later.

- **maxPriorityFeePerGas**:

  Tip to give the miner (per gas, in Wei). The real tip is either this value or 
  **maxFeePerGas-baseFee** (the lower of the two). Available in London and later.

- **value**:

  The value the transaction transmits in Wei


- **to**:

  The destination address, typically a contract


- **secretKey**:

  The secret key for the sending address. That address is derived from the
  secret key and therefore does not need to be specified explicitely
  (`see here 
  <https://www.freecodecamp.org/news/how-to-create-an-ethereum-wallet-address-from-a-private-key-ae72b0eee27b/>`_). 


- **nonce**:

  The nonce value for the transaction. The first transaction for an address
  has the nonce value of the address itself, the second transaction has the
  nonce plus one, etc. Alternatively, if you replace all the **nonce** values
  with **auto**, the tool does this for you.


- **invalid**:

  If the transaction is invalid, meaning clients should reject it, set this value to "1"
