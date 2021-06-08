.. _vm_filler:

=================================
Virtual Machine Tests Source Code
=================================
Location: `src/VMTestsFiller
<https://github.com/ethereum/tests/tree/develop/src/VMTestsFiller>`_

Virtual machine tests check a single instance of EVM execution, with one stack
and one memory space. They are similar to state transition tests, but even 
simpler.

.. note::
   Even though virtual machine tests are in a separate directory under **src**,
   **retesteth** treats them as though they were under 
   **src/BlockchainTestsFiller/ValidBlocks**. For example, this is the command to
   fill and run the **VMTests/vmLogTest/log4_PC** `(link)
   <https://github.com/ethereum/tests/blob/develop/src/VMTestsFiller/vmLogTest/log4_PCFiller.json>`_ 
   test.

   ::

      ./dretesteth.sh -t BlockchainTests/ValidBlocks/VMTests/vmLogTest --    \
        --singletest log4_PC --testpath ~/tests --datadir /tests/config --filltests


.. _vm_src:
.. include:: ../test_filler/test_src.rst

.. _vm_struct:
.. include:: ../test_filler/test_structure.rst


.. _vm_env:
.. include:: ../test_filler/test_env.rst


.. _vm_pre:
.. include:: ../test_filler/test_pre.rst


.. _vm_exec:
.. include:: ../test_filler/test_exec.rst


.. _vm_expect:
.. include:: ../test_filler/test_expect_vm.rst

