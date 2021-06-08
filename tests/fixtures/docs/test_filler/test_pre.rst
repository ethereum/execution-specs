Pre
======
This section contains the initial information of the blockchain.



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
                 "pre": {
                    "address 1": {
			"balance": "0xba1a9ce000",
			"nonce": "0",
			"code": ":raw 0x600160010160005500"
			"storage: {
				"0":       "12345",
				"0x12": "0x121212"
                    },
                    "address 2": {
                        <address fields go here>
                    }
                 }
              }
           }          


     -

       ::

           name-of-test:
              <other sections>
              pre:
                address 1:
		  balance: 0xba1a9ce000,
		  nonce: 0,
		  code: :raw 0x600160010160005500
		  storage:
		    0:       12345
		    0x12: 0x121212
                address 2:
                  <address fields go here>


Address Fields
--------------

.. include:: ../test_filler/test_addr_pre.rst
