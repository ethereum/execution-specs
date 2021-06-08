Blocks
======
This section contains the blocks of the blockchain that are supposed to modify the
state from the one in the **pre** section to the one in the **expect** section.


Format
------

.. list-table::
   :header-rows: 1

   * - JSON

     - YAML

   * -

       ::

           {
              "name-of-test": {
                 <other sections>,
                 blocks: [
                   { transactions: [
                       { <transaction> },
                       { <transaction> }
                     ]
                   },
                   { transactions: [
                       { <transaction> },
                       { <transaction> }
                     ]
                     blockHeader: {
                        "extraData" : "0x42",
                        "gasLimit" : "0x2fefd8",
                        "gasUsed" : "0x5208",
                     },
                     uncleHeaders: [ <values here> ]
                   }
                 ]
              }
           }          


     -

       ::

           name-of-test:
              <other sections>
              blocks:
              - transactions:
                - <transaction>
                - <transaction>
              - blockHeader:
                    extraData: 42
                    gasLimit: 100000
                    gasUsed: 2000
                uncleHeaders:
                  <values here>
                transactions:
                - <transaction>
                - <transaction>

Fields
------
The fields in each block are optional. Only include those fields you need.

- **blockHeader**:

  This field contains the block header parameters. Parameters that are missing are
  copied from the genesis block.

  .. include:: ../test_filler/test_blockheader.rst

  One field inside the block header which is not standard in Ethereum is 
  **expectException**. That field, which is only used in invalid block tests,
  identifies the exception we expect to receive for the block on different
  forks of Ethereum. You can read more about it in the `Invalid Block Tests 
  section of the Blockchain Tests 
  tutorial <../blockchain-tutorial.html#invalid-block-tests>`_.

  Note that starting with London **gasLimit** cannot be changed by more than 1/1024
  from the previous value because of `EIP 1559 <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1559.md>`_.
  You can specify **baseFee**, but the block is only valid if it is the same value
  that was calculated from the previous block.

- **blocknumber** and **chainname**:

  If you are testing behavior in the presence of multiple competing chains,
  these fields let you specify the chain and the block's location within
  it.

- **uncleHeaders**:

  A list of the `uncle blocks (blocks mined at the same time) 
  <https://www.investopedia.com/terms/u/uncle-block-cryptocurrency.asp>`_.
  Each item in the list has two fields:
 
  - **chainname**: The name of the chain from which the uncle block comes

  - **populateFromBlock**: The block number within that chain for the block
    that is an uncle of the block you are specifying.

  However, if you write a test with uncles, you need to run it twice, once
  to get the state hash values to write them in the test filler file, and 
  again to actually run the test.

- **transactions**:

  A list of transaction objects in the block. 
