.. _gstate_tests:


==================================
Generated State Transition Tests
==================================



Location `/GeneralStateTests <https://github.com/ethereum/tests/tree/develop/GeneralStateTests>`_


Test Structure
==============

Contains **transactions** that are to be executed on a state **pre** given the environment **env** and must end up with post results **post**

Although its a simple transaction execution on stateA to stateB, due to the generation of this tests into blockchain format, the transaction execution is performed as if it was a single block with single transaction. This means that mining reward and touch rules after EIP-161 are applied. (mining reward is 0)


* A test file must contain **only one** test `testname`
* Test file name must be **identical** for the test name `testname`


::

  {
    "testname" : {
      "_info" : { ... },
      "env" : { ... },
      "post" : { ... },
      "pre" : { ... },
      "transaction" : { ... }
    }
  }

.. _info_gstate:
.. include:: ../test_types/TestStructures/info.rst
.. _env_gstate:
.. include:: ../test_types/TestStructures/GeneralStateTests/env.rst
.. _post_gstate:
.. include:: ../test_types/TestStructures/GeneralStateTests/post.rst
.. _pre_gstate:
.. include:: ../test_types/TestStructures/pre.rst
.. _transaction_vrs_gstate:
.. include:: ../test_types/TestStructures/GeneralStateTests/transaction.rst
