.. retesteth_ref:

#######################
Using Retesteth
#######################


Command Line Options
========================

.. note::

   There has to be a double dash (**-\\-**) between the **-t** option that sets the
   suite and all the other options.
   

Set The Suite
-----------------------
============================================= ===================================
**Option**                                    **Meaning**
============================================= ===================================
-t <TestSuite>                                Run all the tests in that suite

-t <TestSuite>/<Test Case Folder>             Run a specific test case folder
                                              (for **GeneralStateTests**)

-t <TestSuite>/<Test Type>/<Test Case Folder> Run a specific test case folder
                                              (for **BlockchainTests**)
============================================= ===================================

.. note:: 

   In **BlockchainTests** there are three possible values for the test type:
                                              
   - **ValidBlocks**  
   - **InvalidBlocks**
   - **TransitionTests**


Retesteth Options
-----------------------

================================= ======================================================
**Option**                        **Meaning**                                        
================================= ======================================================
 -j <ThreadNumber>                Run test execution using threads                    
 -\\-clients `client1, client2`   Use following configurations from                     
                                  datadir path (default: ~/.retesteth)                 
 -\\-datadir                      Path to configs (default: ~/.retesteth)            
 -\\-nodes                        List of client tcp ports ("addr:ip, addr:ip")      
 -\\-help -h                      Display list of command arguments                  
 -\\-version -v                   Display build information                          
 -\\-list                         Display available test suites                      
================================= ======================================================


.. note::

   Setting **-\\-nodes** overrides the **socketAddress** section of the **config** file,
   `documented here 
   <https://ethereum-tests.readthedocs.io/en/latest/config-dir.html#socketaddress>`_.


Setting the Test Suite and Test
----------------------------------
========================================= ===================================================
Option                                    Meaning
========================================= ===================================================
-\\-testpath <PathToTheTestRepo>          Set path to the test repo
-\\-testfile <TestFile>                   Run tests from a file. Requires -t <TestSuite>
-\\-singletest <TestName>                 Run on a single test. `Testname` is the filename 
                                          without Filler.<type> (either **json** or **yml**)
-\\-singletest <TestName>/<Subtest>       `Subtest` is a test name inside the file.
========================================= ===================================================

.. note::

   **<Subtest>** is only relevant in **BlockchainTests**. Other test suites
   do not support files with multiple test names.


Debugging
----------------------------------

============================= ===================================================
Option                        Meaning
============================= ===================================================
-d <index>                    Set the transaction data array index when running 
                              GeneralStateTests
-g <index>                    Set the transaction gas array index when running 
                              GeneralStateTests
-v <index>                    Set the transaction value array index when running 
                              GeneralStateTests
-\\-vmtraceraw                Trace transaction execution
-\\-vmtrace                   Trace transaction execution, simplified version
-\\-limitblocks <num>         Limit the block exectuion in blockchain tests for 
                              debugging to the first <num> blocks
-\\-limitrpc                  Limit the rpc exectuion in tests for debug
-\\-verbosity <level>         Set logs verbosity. 0 - silent, 1 - only errors, 
                              2 - informative, >2 - detailed
-\\-exectimelog               Output execution time for each test suite
-\\-statediff                 Trace state difference for state tests
-\\-stderr                    Redirect ipc client stderr to stdout
-\\-travisout                 Output \`.\` to stdout
============================= ===================================================
    
Additional Tests
----------------------------------

======================================= ===================================
Option                                  Meaning
======================================= ===================================
-\\-all                                 Enable all tests
-\\-lowcpu                              Disable cpu intensive tests
======================================= ===================================



Test Generation
----------------------------------

=============================== ===================================
Option                          Meaning
=============================== ===================================
-\\-filltests                   Run test fillers
-\\-fillchain                   When filling the state tests, fill 
                                tests as blockchain instead
-\\-showhash                    Show filler hash debug information
-\\-poststate                   Show post state hash or fullstate
-\\-fullstate                   Do not compress large states to hash
=============================== ===================================



Examples
===================
These examples assume you configured your enviroment `the way it was
shown in the tutorial 
<https://ethereum-tests.readthedocs.io/en/latest/retesteth-tutorial.html>`_
and that you are in your home directory.
If you used different directories, or did not use docker, the commands
will be slightly different.


#. Run most state tests:

   ::

     ./dretesteth.sh -t GeneralStateTests -- --testpath ~/tests

   Run multiple tests simultaneously:

   ::

     ./dretesteth.sh -t GeneralStateTests -- --testpath ~/tests -j 8

   Run all the tests including the time consuming ones:

   ::

     ./dretesteth.sh -t GeneralStateTests -- --testpath ~/tests -all


#. Run most blockchain tests:

   ::

      ./dretesteth.sh -t BlockchainTests -- --testpath ~/tests

   Run only the valid blocks tests:

   ::

      ./dretesteth.sh -t BlockchainTests/ValidBlocks -- --testpath ~/tests

   Run only the invalid blocks tests:

   ::

      ./dretesteth.sh -t BlockchainTests/InvalidBlocks -- --testpath ~/tests

   Run only a specific suite of tests:

   ::

      ./dretesteth.sh -t BlockchainTests/ValidBlocks/bcGasPricerTest \
           -- --testpath ~/tests

   Run only the tests in a specific file (typically there would only be one):

   ::

      ./dretesteth.sh -t BlockchainTests/ValidBlocks/bcGasPricerTest \
           -- --testpath ~/tests --singletest highGasUsage

   Run a specific test from a specific file:

   ::

      ./dretesteth.sh -t BlockchainTests/InvalidBlocks/bcForgedTest \
           -- --testpath ~/tests \
           --singletest bcBlockRLPAsList/BLOCK_difficulty_GivenAsList_Byzantium
  



#. Run transition tests (tests that verify the transition from one 
   fork to the next is implemented correctly):

   ::

      ./dretesteth.sh -t BlockchainTests/TransitionTests -- --testpath ~/tests

   Run the tests for a specific transition (in this case **Byzantium** to 
   **ConstantinopleFix**):

   ::

      ./dretesteth.sh -t \
        BlockchainTests/TransitionTests/bcByzantiumToConstantinopleFix -- \
        --testpath ~/tests
   
   .. note::

      Not all transitions have associated test cases. To see which test
      cases are avaliable, run:

      ::

        ls tests/BlockchainTests/TransitionTests


#. Run a test from your own file:

   ::

     ./dretesteth.sh -t GeneralStateTests -- --testpath ~/tests \
         --testfile tests/GeneralStateTests/stExample/add11.json

   .. note::

      In this case the test is part of the test suite and there are 
      easier ways to run it. However, you can use **-\\-testfile** for 
      files that are located elsewhere.
      You can mount any directory inside the docker 
      (using **-\\-testpath**), and it will appear in
      the docker as **/tests**.


#. Fill tests. So far all of the examples have been using the generated,
   filled test files. However, you can also use the test source code
   (a.k.a. the filler version).

   Fill (and run) a test that is part of the test suite (in this case,
   **tests/GeneralStateTests/stExample/add11**, whose source code is
   **tests/src/GeneralStateTestsFiller/stExample/add11Filler.json**):

   ::
 
      ./dretesteth.sh -t GeneralStateTests/stExample -- \
        --testpath ~/tests --singletest add11 --filltests

   Combine this option with **-\\-testfile** to fill and run your
   own tests: 

   ::

      ./dretesteth.sh -t GeneralStateTests -- --testpath ~ --filltests \
          --testfile tests/tests/docs/tutorial_samples/01_add22Filler.yml


#. Run a test on a specific network (fork, such as **Istanbul** or
   **Berlin**):

   ::

     ./dretesteth.sh -t BlockchainTests/ValidBlocks/bcStateTests -- \
         --testpath ~/tests --singletest simpleSuicide --filltests  \
         --singlenet Berlin

   .. note::

      The generated files usually contain tests for the current fork.
      If you want to test a different fork, as we do here, it may be
      necessary to use **-\\-filltests**.


#. Run a single test from a `multitest file 
   <https://ethereum-tests.readthedocs.io/en/latest/state-transition-tutorial.html#multitest-files>`_. The actual values come from the test file, the 
   parameters you specify (**-d**, **-g**, and **-v**) are indexes into their 
   respective lists (data, gas, and transaction value):

   ::

      ./dretesteth.sh -t GeneralStateTests -- --testpath ~/tests --filltests \
         --testfile /tests/docs/tutorial_samples/04_multitestFiller.yml -d 1

#. Run a test and produce `a trace of the Ethererum Virtual Machine:
   <https://ethereum-tests.readthedocs.io/en/latest/internals-tutorial.html#virtual-machine-trace>`_:

   ::

      ./dretesteth.sh -t GeneralStateTests/stExample -- \
           --testpath ~/tests --vmtrace

   Proudce a more detailed, but less readable, trace:

   ::

      ./dretesteth.sh -t GeneralStateTests/stExample -- \
           --testpath ~/tests --vmtraceraw


#. Run a test and dump the state (accounts balances, storage, etc.) at the end of it:

   ::

      ./dretesteth.sh -t GeneralStateTests/stExample -- --testpath ~/tests --poststate

