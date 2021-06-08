.. _sample_abi_tests:


=================================
ABI Tests
=================================

Location `/ABITests/basic_abi_tests.json 
<https://github.com/ethereum/tests/blob/develop/ABITests/basic_abi_tests.json>`_

A number of test cases for the `application binary interface
<https://solidity.readthedocs.io/en/v0.7.1/abi-spec.html>`_. These test cases only 
include the encoded arguments, not the the first four bytes, which are a hash of the function 
name and parameter types. 

The format of each test value is:

::

    "<name of test>": {

The data types of the arguments, a list of strings.

:: 

       "types": [
          "uint256",
          "bytes",
          "uint32[]"
       ],

The values of the arguments. These can be integers, strings, or arrays:

::

       "args": [
          0xda7a0000da7a0000,
          "a string",
          [16, 256]
       ],

The encoded arguments, a hexadecimal string:

::

       "result": "000000000000000000000000000000000000000000000000da7a0000da7a0000000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000086120737472696e67000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000100"
       }
