Expect
======
This section contains the information we expect to see after the test is 
concluded. Virtual machine tests use a simplified version, which 
includes only one address and for that address only the storage.


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
                 "expect": {
                    "address in exec section": {
                       "storage": {
                         "0":    "0x00112233",
                         "0x10": "31415"
                       }
                    }
                 }
              }
           }          


     -

       ::

           name-of-test:
              <other sections>
              expect:
                <address in exec>:
                  storage:
                    0: 0x00112233
                    0x10: 31415
