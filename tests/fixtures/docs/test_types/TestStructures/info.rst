
Info Section
================

::

   "_info" : {
            "comment" : "A test for (add 1 1) opcode result",
            "filling-rpc-server" : "Geth-1.9.14-unstable-8cf83419-20200512",
            "filling-tool-version" : "retesteth-0.0.3+commit.672a84dd.Linux.g++",
            "lllcversion" : "Version: 0.5.14-develop.2019.11.27+commit.8f259595.Linux.g++",
            "source" : "src/GeneralStateTestsFiller/stExample/add11Filler.json",
            "sourceHash" : "e474fc13b1ea4c60efe2ba925dd48d6f9c1b12317dcd631f5eeeb3722a790a37"
    },

Info section is generated with the test and contains information about test and it's generators.

**Fields**

========================= ===============================================================================
``comment``                comment from the test source. (can be edited at source)
``filling-rpc-server``     tool that has been used to generate the test (version)
``filling-tool-version``   the test generator (retesteth) version
``lllcversion``            lllc version that was used to compile LLL code in test fillers
``source``                 path to the source filler in the test repository
``sourceHash``             hash of the json of source file (used to track that tests are updated)
========================= ===============================================================================