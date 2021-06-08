Exec
=============
This is the code and data for the virtual machine to execute.



Format
------------

.. list-table::
   :header-rows: 1

   * - JSON

     - YAML

   * -

       ::

           {
              "name-of-test": {
                 <other sections>,
                 "exec": {
                 }
           }

     - ::

           name-of-test:
              <other sections>
              pre:


Fields
--------------
- **address**:

  The address of the contract the virtual machine is executing

- **caller**:

  The address that called this contract

- **data**:

  The data, either in hexadecimal or an 
  `ABI call <https://solidity.readthedocs.io/en/v0.7.1/abi-spec.html>`_
  with this format:
  
  ::

      :abi <function signature> <function parameters separated by spaces>


- **gas**:
  
  Gas limit for the transaction


- **gasPrice**:

  Gas price in Wei


- **value**:

  The value the transaction transmits in Wei

