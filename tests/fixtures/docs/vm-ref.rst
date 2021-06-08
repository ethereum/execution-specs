Virtual Machine Tests
======================

These tests are similar to state transition tests, but simpler. They can only be used
to test the virtual machine component of an ethereum client.

.. warning::
   These tests only look at the storage after the virtual machine executes. They 
   ignore the virtual machine's output, and any emitted events. If you have a mature
   client and want to test most features, write a state transition test instead.

.. toctree::
   :maxdepth: 2

   test_filler/vm_filler.rst
   test_types/vm_tests.rst
