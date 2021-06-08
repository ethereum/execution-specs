============================= ========================
Name in Block Header Sections Meaning
============================= ========================
bloom                         `bloom filter <https://en.wikipedia.org/wiki/Bloom_filter>`_ to
                              speed searches
coinbase                      beneficiary of mining fee
extraData                     data added to the block, ignored by **retesteth**
difficulty                    difficulty of previous block
gasLimit                      limit of gas usage per block
gasUsed                       gas used by this block
mixHash and nonce             used by the `proof of work algorithm 
                              <https://en.wikipedia.org/wiki/Ethash>`_, ignored by **retesteth**
number                        number of ancestor blocks
parentHash                    hash of previous block
receiptTrie                   The root of the `receipt trie 
                              <https://medium.com/shyft-network-media/understanding-trie-databases-in-ethereum-9f03d2c3325d>`_
                              after this block
stateRoot                     The root of the `state trie 
                              <https://medium.com/@eiki1212/ethereum-state-trie-architecture-explained-a30237009d4e>`_
                              after this block
timestamp                     `Unix time <https://en.wikipedia.org/wiki/Unix_time>`_
transactionTrie               The root of the `transaction trie 
                              <https://medium.com/shyft-network-media/understanding-trie-databases-in-ethereum-9f03d2c3325d>`_
                              after this block
uncleHash                     hash of uncle block or blocks
baseFee                       The base fee per gas required of transactions
                              (London and later, because of 
                              `EIP 1559 <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1559.md>`_)
============================= ========================

`You can read more about the block header fields here
<https://medium.com/@derao512/ethereum-under-the-hood-part-7-blocks-7f223510ba10>`_.

