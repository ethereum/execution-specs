
Pre/preState Section
====================

::

        "pre" : {
            "0x095e7baea6a6c7c4c2dfeb977efac326af552d87" : {
                "balance" : "0x0de0b6b3a7640000",
                "code" : "0x600160010160005500",
                "nonce" : "0x00",
                "storage" : {
                    "0x00" : "0x01"
                }
            },
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b" : {
                "balance" : "0x0de0b6b3a7640000",
                "code" : "0x",
                "nonce" : "0x00",
                "storage" : {
                }
            }
        },

Pre section describes a full state of accounts used in test.

Its a map of <Account> => <AccountFields>

AccountFields are always complete (`balance`, `code`, `nonce`, `storage` must present) in this section and can not have a missing field.

* All values are 0x prefixed hex.
* Empty code defined as 0x.
* Zero storage record defined as 0x00.


**Fields**

======================= ============ ===================================================================
``address hash``         **HASH20**   is 20 bytes ethereum address 0x prefixed
``balance``              **VALUE**    account balance in evm state
``code``                 **BYTES**    account code in evm state
``nonce``                **VALUE**    account nonce in evm state
``storage``              **map**      map of storage records **VALUE** => **VALUE**
======================= ============ ===================================================================

.. include:: types.rst
