
Post Section
============

::

        "post" : {
            "Istanbul" : [
                {
                    "indexes" : {
                        "data" : 0,
                        "gas" : 0,
                        "value" : 0
                    },
                    "hash" : "0xe4c855f0d0e96d48d73778772ee570c45acb7c57f87092e08fed6b2205d390f4",
                    "logs" : "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
                }
            ]
        },

Post section is a map `<FORK> => [TransactionResults]`

The test can have many fork results and each fork result can have many transaction results.

In generated test indexes are a single digit and could not be array. Thus define a single transaction from the test.
See transaction section which define transactions by `data`, `gasLimit`, `value` arrays.


**Fields**

======================= ===============================================================================
``Istanbul``             fork name as defined by client config (test standard names)
``indexes``              define an index of the transaction in txs vector that has been used for this result
``data``                 index in transaction data vector
``gas``                  index in transaction gas vector
``value``                index in transaction value vector
``hash``                 hash of the post state after transaction execution
``logs``                 log hash of the transaction logs
======================= ===============================================================================