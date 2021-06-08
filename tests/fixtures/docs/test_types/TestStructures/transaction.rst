
Transaction Section
===================

::

    {
        "transaction" : {
            "data" : "0x",
            "gasLimit" : "0x061a80",
            "gasPrice" : "0x01",
            "nonce" : "0x00",
            "secretKey" : "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8",
            "to" : "0x095e7baea6a6c7c4c2dfeb977efac326af552d87",
            "value" : "0x0186a0"
        }
    },
    {
        "transaction" : {
            "data" : "0x",
            "gasLimit" : "0x061a80",
            "gasPrice" : "0x01",
            "nonce" : "0x00",
            "v" : "0x1c",
            "r" : "0x3d55a2ac293c7ad82632b18705e67ad2a0e6177d44f601dca043934c8cd8c07a",
            "s" : "0x1c069ed47162b350a1f496e9a55f53685189e9c3076a4931334a43719b9a158e",
            "to" : "",
            "value" : "0x0186a0"
        }
    }

Transaction section defines single transaction to be executed in BlockchainTest's block.

* All fields are 0x prefixed HEX of even length (can be like 0x0122)
* empty data is defined as 0x
* transaction creation `to` defined as ""

.. Note::
   Fields `r`, `s` are u256 and can be less than 32 bytes!

.. Note::
   There is an EIP limiting `s` max value (source?). From a certain fork transactions with `s` value > `sMaxValue` are considered to be invalid.


**Fields**

============= ========== ===============================================================================
``data``      **BYTES**  data/input code of the transaction
``gasLimit``  **VALUE**  gasLimit of transaction.
``gasPrice``  **VALUE**  Transaction's gas price
``nonce``     **VALUE**  Transaction's nonce
``secretKey`` **HASH32** SecretKey criptic value used to sign tx data by v,r,s
``v``         **VALUE**  Cryptic value ``1 byte in length``
``r``         **VALUE**  Values corresponding to the signature of the transaction and used to determine the sender of the transaction.
``s``         **VALUE**  Values corresponding to the signature of the transaction and used to determine the sender of the transaction.
``to``        **FH20**   Transaction's `to` destination address. ``set to "" if creation``.
``value``     **VALUE**  Value of the transaction.
============= ========== ===============================================================================

.. include:: types.rst