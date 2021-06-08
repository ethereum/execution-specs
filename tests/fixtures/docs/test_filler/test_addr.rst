- **balance**:

  Wei balance at the start of the test

- **code**:

  The code of the contract. In the **expect:** section this has to
  be raw virtual machine code.

- **nonce**:

  The `nonce counter <https://en.wikipedia.org/wiki/Cryptographic_nonce>`_ for the address.
  This value is used to make sure each transaction is processed only once. The first transaction
  the address sends has a nonce equal to this value, the second one is the nonce plus one, etc.

- **storage**:

  Values in the storage of the address

  .. list-table::
     :header-rows: 1

     * - JSON

       - YAML

     * -

         ::

            storage: {
		"1": 5, 
		"0x20": 0x10
	    }

       -

         ::

            storage:
               1: 5
               0x20: 0x10

