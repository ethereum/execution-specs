
Transaction Section
===================

::

        "transaction" : {
            "data" : [
                "0x"
            ],
            "gasLimit" : [
                "0x061a80"
            ],
            "gasPrice" : "0x01",
            "nonce" : "0x00",
            "secretKey" : "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8",
            "to" : "0x095e7baea6a6c7c4c2dfeb977efac326af552d87",
            "value" : [
                "0x0186a0"
            ]
        }

Transaction section defines a vector of transaction to be executed in GeneralStateTest
From this section it is possible to construct many transaction using values from data,gasLimit,value array. Indexes in this array used in the post section to point out which transaction has been used to calculate the post state hash.

* All fields are 0x prefixed HEX of even length (can be like 0x0122)
* empty data is defined as 0x
* transaction creation `to` defined as ""


**Fields**

================= ================ ==============================================================
``data``          array(**BYTES**) Array of data/input of transaction. In Post section indexes::data index indicates index in this array.
``gasLimit``      array(**VALUE**) Array of gasLimit of transaction. In Post section indexes::gas index indicates index in this array
``gasPrice``      **VALUE**        Transaction's gas price
``nonce``         **VALUE**        Transaction's nonce
``secretKey``     **FH32**         SecretKey criptic value used to sign tx data by v,r,s
``to``            **FH20**         Transaction's `to` destination address. set to "" if creation.
``value``         **VALUE**        Array of value of transaction. In Post section indexes::value index indicates index in this array
================= ================ ==============================================================