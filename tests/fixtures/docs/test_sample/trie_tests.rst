.. _sample_trie_tests:


=================================
Trie Tests
=================================

Location `/TrieTests/
<https://github.com/ethereum/tests/tree/develop/TrieTests>`_

These are sample `trie structures 
<https://medium.com/shyft-network-media/understanding-trie-databases-in-ethereum-9f03d2c3325d>`_.

This is the format of most of those tests:

::

  {
    "name of test": {
      "in": [
        ["do", "verb"],
        ["ether", "wookiedoo"],
        ["horse", "stallion"],
        ["shaman", "horse"],
        ["doge", "coin"],
        ["ether", null],
        ["dog", "puppy"],
        ["shaman", null]
      ],
      "root": "0x29b235a58c3c25ab83010c327d5932bcf05324b7d6b1185e650798034783ca9d"
    }
  }


The fields are:

- **in**, The data to store in the trie, which can be either a 
  `map object <https://en.wikipedia.org/wiki/Associative_array>`_ or a
  list in which each item contains a list of a key and the corresponding value.

- **root**, the hash expected at the root of the trie after adding all of those
  items

- **hexEncoded** (optional), if this field exists and is **true**, it 
  means the strings for the keys and values are already encoded hexadecimal, rather than
  ASCII strings.




Next and Previous Test
======================
The test `/TrieTests/trietestnextprev.json 
<https://github.com/ethereum/tests/blob/develop/TrieTests/trietestnextprev.json>`_ 
is formatted differently. Instead of testing the entire trie data structure, this
file is used to test individual operations within this structure.
