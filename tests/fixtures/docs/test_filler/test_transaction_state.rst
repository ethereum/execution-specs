Transaction
=============

This is the data of the transaction.


Format
------------


.. list-table::
   :header-rows: 1

   * - JSON

     - YAML

   * -

       ::

           {
               "name-of-test": {
                  <other sections>,
                  "transaction":
                     {
                        "data": ["0xDA7A", "0xDA7A", ":label hex 0xDA7A", 
                             ":abi f(uint) 0xDA7A",
                             {
                                  "data": "0xDA7A", 
                                  "accessList": [ 
                                     {
                                        "address": "0x0000000000000000000000000000000000000101",
                                        "storageKeys": [0x60A7, 0xBEEF]
                                     },
                                     {
                                        "address": "0x0000000000000000000000000000000000000102"
                                     }
                                  ]
                              }
                        ],
                        "gasLimit": ["0x6a506a50"],
                        "value": ["1"],
                        "to": "add13ess01233210add13ess01233210",
                        "secretKey": "5ec13e7 ... 5ec13e7"
                        "nonce": '0x909ce'
                        "maxPriorityFeePerGas": "10",
                        "maxFeePerGas": "2000",
           }

     - ::

           name-of-test:
             <other sections>
             transaction:
               data:
               - 0xDA7A
               - 0xDA7A
               - :label hex 0xDA7A
               - :abi f(uint) 0xDA7A
               - data: :label acl 0xDA7A
                 accessList:
                 - address: 0x0000000000000000000000000000000000000101
                   storageKeys: 
                   - 0x60A7
                   - 0xBEEF
                 - address: 0x0000000000000000000000000000000000000102
               gasLimit:
               - '0xga50ga50'
               value: 
               - "1"
               to: "add13ess01233210add13ess01233210"
               secretKey: "5ec13e7 ... 5ec13e7"
               nonce: '0x909ce'
               maxPriorityFeePerGas: 10
               maxFeePerGas: 2000


Fields
--------------
- **data**:

  The data, either in hexadecimal or an 
  `ABI call <https://solidity.readthedocs.io/en/v0.7.1/abi-spec.html>`_
  with this format:
  **:abi <function signature> <function parameters separated by spaces>**.
  The value can also be labeled:
  **:label <value>**. 
  This value is specified as a list to enable
  `files with multiple tests <../state-transition-tutorial.html#multitest-files>`_

  The data can also have an `EIP2930 
  <https://eips.ethereum.org/EIPS/eip-2930>`_ access list. In that case the data
  field itself is a structure with two fields: **data** (the data) and **accessList**.
  The **accessList** is a list of structures, each of which has to have an **address**
  and may have a list of **storageKeys**.

- **gasLimit**:
  
  Gas limit for the transaction.
  This value is specified as a list to enable
  `files with multiple tests <../state-transition-tutorial.html#multitest-files>`_


- **gasPrice**:

  Gas price in Wei, only in Berlin and earlier 
  (replaced by maxFeePerGas in London)


- **value**:

  The value the transaction transmits in Wei.
  This value is specified as a list to enable
  `files with multiple tests <../state-transition-tutorial.html#multitest-files>`_


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
  nonce plus one, etc.

- **maxPriorityFeePerGas**:
  
  The maximum priority fee per gas (a.k.a. tip) the transaction is willing to pay to
  be included in the block (London and later, `added by 
  eip 1559 <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1559.md>`_).

- **maxFeePerGas**:
  
  The maximum total fee per gas the transaction is willing to pay to
  be included in the block (London and later, `added by 
  eip 1559 <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1559.md>`_).


