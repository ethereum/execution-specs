Expect
======
This section contains the information we expect to see after the test is 
concluded.


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
                 "expect": [
                   {
                      "indexes": {
                        "data": [0, "2-3", ":label foo"],
                        "gas": -1,
                        "value": -1
                      },
                      "network": ["Istanbul", <other forks, see below>],
                      "result": {
                           "address 1": {
                               "balance": "0xba1a9ce000",
                               "nonce": "0",
                               "storage: {
                                   "0x0":     12345,
                                   "10" : "0x121212"
                               },
                               "code": "0x00"
                           },
                           "address 2": {
                               <address fields go here>
                           }
                   },
                   { <forks & results> }
                 ]
              }
           }          


     -

       ::

           name-of-test:
              <other sections>
              expect:
              - indexes:
                  data:
                  - !!int 0
                  - 2-3
                  - :label foo
                  gas: !!int -1
                  value: !!int -1
                network:
                - Istanbul
                - <another fork>
                result:
                  address 1:
                    balance: 0xba1a9ce000,
                    nonce: 0,
                    storage:
                      0x0:  12345
                      10: 0x121212
                    code: 0x00      
                  address 2: 
                     <address fields go here>
              - <forks & results>


The Network Specification
-------------------------
The string that identifies a fork (version) within a **network:** 
list is one of three option:

- The specific version: **Istanbul**
- The version or anything later: **>=Frontier**
- Anything up to (but not including) the version **<Constantinople**



The Indexes
-----------
The transaction can have multiple values for **data**, **gasLimit**, and 
**value**. The **indexes:** section specifies which of these values 
are covered by a particular item in **expect**, for each field it can be
either a single specification or a list of specifications. Each of those 
specifications uses any of these options:

.. list-table::
   :header-rows: 1

   * - JSON

     - YAML

     - Meaning

   * - -1
 
     - !!int -1
  
     - All the (**data**, **gas**, or **value**) values in the transaction

   * - <n>

     - !!int <n>

     - The n'th value in the list (counting from zero)

   * - "<a>-<b>"

     - a-b

     - Everthing from the a'th value to the b'th value (counting from zero)

   * - ":label foo"

     - :label foo

     - Any value in the list that is specified as **:label foo <value>**




Address Fields
--------------
It is not necessary to include all fields for every address. Only include those
fields you wish to test.

.. include:: ../test_filler/test_addr.rst

