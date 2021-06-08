.. _retesteth_tutorial:

==============================
Retesteth
==============================

`Ori Pomerantz <mailto://qbzzt1@gmail.com>`_

.. note::
    This document is a tutorial. For reference on the
    **retesteth** options, `look
    here <https://ethereum-tests.readthedocs.io/en/latest/retesteth-ref.html>`__.


Retesteth through the Web
=========================
The easiest way to run the tests is through `the web interface 
<http://retesteth.ethdevops.io/web/>`_. 

Request Helper
--------------
To run an existing `state test 
<https://ethereum-tests.readthedocs.io/en/latest/state-transition-tutorial.html>`_,
you can use the **request helper**. You set these parameters:

==================    ================ ============
Parameter             Meaning          Sample Value
==================    ================ ============
GeneralStateTests/    test suite       stExample
-\\-singletest        name of test     add11
-\\-clients           client to use    t8ntool (the value for geth)
-\\-singlenet         fork to use      Berlin
-\\-vmtrace           trace to produce raw
-\\-verbosity         log verbosity    none
==================    ================ ============

When a test file contains `multiple tests 
<https://ethereum-tests.readthedocs.io/en/latest/state-transition-tutorial.html#multitest-files>`_
you can restrict which ones you'll run with the **-d**, **-g**, and **-v** 
parameters.



Request Single File
-------------------
You can run a single test, either state test or `blockchain test 
<https://ethereum-tests.readthedocs.io/en/latest/blockchain-tutorial.html>`_,
using the **request single file** option. You specify the test type
and then upload a test file. Here are the parameters:


==================    ================= ============
Parameter             Meaning           Sample Value
==================    ================= ============
-t                    test suite        test type (state or blockchain)
-\\-testfile          The file to test  you upload this file
-\\-clients           client to use     t8ntool (the value for geth)
-\\-vmtrace           trace to produce  raw
-\\-filltests         test file type    see below
==================    ================= ============

If -\\-filltests is set to **none**, you need to upload a generated test file.
You can find those `here (for state tests) 
<https://github.com/ethereum/tests/tree/develop/GeneralStateTests>`_, and 
`here (for blockchain tests) 
<https://github.com/ethereum/tests/tree/develop/BlockchainTests>`_.

If -\\-filltests is set to **filltests** then you can upload a filler test file,
which you can write yourself. This is documented 
`in this tutorial (for state tests) 
<https://ethereum-tests.readthedocs.io/en/latest/state-transition-tutorial.html>`_ 
and `this one (for blockchain tests) 
<https://ethereum-tests.readthedocs.io/en/latest/blockchain-tutorial.html>`_.



Custom Command
--------------
The command line parameters for **retesteth** are documented
`here <https://ethereum-tests.readthedocs.io/en/latest/retesteth-ref.html>`_.
You can use this option to run whatever parameters you want.
 

Retesteth in a Docker Container
===============================
If you want to run the tests locally you can 
run **retesteth** inside a Docker container.


.. include:: retesteth-install.rst


How Does This Work?
-------------------
A `docker <https://www.docker.com/resources/what-container>`__ container
is similar to a virtual machine, except that it doesn't run a separate
instance of the operating system inside itself so it takes far less
resources. One of the features of docker is that it can mount a
directory of the host computer inside its own file system. The
**-\\-testpath** parameter to **dretesteth.sh** tells it what directory to
mount, in this case **~/tests** which you just cloned from github. It
mounts it as **/tests** inside the container.

By default the **retesteth** configuration files are in
**~/.retesteth**. However, that directory is not accessible to us
outside the docker. Instead, we use **-\\-datadir /tests/config** to tell
it to use (or create) the configuration in what appears to us to be
**~/tests/config**, which is easily accessible.

Test Against Your Client
========================
There is an instance of **geth** inside the docker container that you
can run tests against. However, unless you are specifically developing
tests what you want is to test your client. There are several ways to do
this:

-  Keep the client on the outside and keep the configuration files
   intact
-  Put your client, and any prerequisites, inside the docker and change
   the configuration files
-  Keep your client on the outside and connect to it through the network
   and change the configuration files

When we ran the test in the previous section we also created those
configuration files in **~/tests/config**, but they were created as
being owned by root. If you need to edit them, change the permissions of
the config files. To change the configuration files to your own user,
run this command: 

::

    sudo find ~/tests/config -exec chown $USER {} \; -print

If you look inside **~/tests/config**, you'll see a directory for each
configured client. Typically this directory has these files:

-  **config**, which contains the configuration for the client:

   -  The communication protocol to use with the client (typically TCP)
   -  The address(es) to use with that protocol
   -  The forks the client supports
   -  The exceptions the client can throw, and how **retesteth** should
      interpret them. This is particularly important when testing the
      client's behavior when given invalid blocks.

-  **start.sh**, which starts the client inside the docker image
-  **stop.sh**, which stops the client instance(s)
-  **genesis**, a directory which includes the genesis blocks for
   various forks the client supports. If this directory does not exist
   for a client, it uses the genesis blocks for the default client.

`Click here for additional documentation. Warning: 
This documentation may not be up to date
<https://github.com/ethereum/retesteth/wiki/Add-client-configuration-to-Retesteth>`__

Client Outside the Docker, Keep Configuration Files Intact
----------------------------------------------------------
If you want to run your client outside the docker without changing the
configuration, these are the steps to follow.

#. Make sure that the routing works in both directions (from the docker
   to the client and from the client back to the docker). You may need
   to configure `network address
   translation <https://www.slashroot.in/linux-nat-network-address-translation-router-explained>`__.

#. Run your client. Make sure that the client accepts requests that
   don't come from **localhost**. For example, to run **geth** use:

   ::

      geth --http --http.addr 0.0.0.0 retesteth

   To run **besu** use:

   ::

      
      docker run -p 8545:8545 -p 13001:30303 \
           hyperledger/besu:latest retesteth --rpc-http-port 8545 \
           --host-allowlist '*'

#. Run the test the same way you would for a client that runs inside
   docker, but with the addition of the **-\\-nodes** parameter. Also,
   make sure the **-\\-clients** parameter is set to the client you're
   testing.

   :: 

      ./dretesteth.sh -t BlockchainTests/ValidBlocks/VMTests -- \
         --testpath ~/tests --datadir /tests/config --clients geth \
         --nodes \<ip\>:\<port, usually defaults to 8545\>

Client Inside the Docker, Modify Configuration Files
----------------------------------------------------

If you want to run your client inside the docker, follow these steps:

#. Move the client into **~/tests**, along with any required
   infrastructure (virtual machine software, etc). If you just want to
   test the directions right now, `you can download geth
   here <https://geth.ethereum.org/downloads/>`_.
#. Modify the appropriate **start.sh** to run your version of the client
   instead. For example, you might edit **~/tests/config/geth/start.sh**
   to replace **geth** with **/tests/geth** in line ten if you put your
   version of **geth** in **~/tests**.
#. Run the tests, adding the **-\\-clients \<name of client\>** parameter to
   ensure you're using the correct configuration. For example, run this
   command to run the virtual machine tests on **geth**: 

   ::

      ./dretesteth.sh -t BlockchainTests/ValidBlocks/VMTests -- --testpath \
      ~/tests --datadir /tests/config --clients geth

Client Outside the Docker, Modify Configuration Files
-----------------------------------------------------
If you want to run your client outside the docker and specify the
connectivity in the configuration files, these are the steps to follow:

#. Create a client in **~/tests/config** that doesn't have **start.sh**
   and **stop.sh**. Typically you would do this by copying an existing
   client, for example: 

   ::

      mkdir ~/tests/config/gethOutside 
      cp ~/tests/config/geth/config ~/tests/config/gethOutside

#. If you want to specify the IP address and port in the **config**
   file, modify the host in the **socketAddress** to the appropriate
   remote address. This address needs to work with the `JSON over RPC
   test protocol <https://en.wikipedia.org/wiki/JSON-RPC>`_.

   For example, 

   ::

 
      { 
         "name" : "Ethereum GO on TCP", 
         "socketType" : "tcp", 
         "socketAddress" : [ "10.128.0.14:8545" ],
         ...
      }

#. Make sure that the routing works in both directions (from the docker
   to the client and from the client back to the docker). You may need
   to configure `network address
   translation <https://www.slashroot.in/linux-nat-network-address-translation-router-explained>`__.
#. Run your client. Make sure that the client accepts requests that
   don't come from **localhost**. For example, to run **geth** use:


   ::

      geth --http --http.addr 0.0.0.0 retesteth

#. Run the test the same way you would for a client that runs inside
   docker: 

   ::

      ./dretesteth.sh -t BlockchainTests/ValidBlocks/VMTests -- \
          --testpath ~/tests --datadir /tests/config --clients gethOutside

Running Multiple Threads
========================
To improve performance you can run tests across multiple threats. To do
this: 

#. If you are using **start.sh** start multiple nodes with
   different ports 
#. Provide the IP addresses and ports of the nodes,
   either in the **config** file or the **--nodes** parameter 
#. Run with the parameters **-j <number of threads>**.


Using the Latest Version
========================
The version of retesteth `published as a docker file 
<http://retesteth.ethdevops.io/>`_
may not have the latest
updates. If you want the latest features, you need to build an image from the
**develop** branch yourself:

#. Install docker.

   ::

      sudo apt install -y wget docker docker.io

#. Download the **dretesteth.sh** script and the **Dockerfile**.

   ::

      wget https://raw.githubusercontent.com/ethereum/retesteth/develop/dretesteth.sh
      chmod +x dretesteth.sh 
      wget https://raw.githubusercontent.com/ethereum/retesteth/develop/Dockerfile

#. Modify the **RUN git clone** line in the **Dockerfile** to change the **-b**
   parameter from **master** to **develop**.

#. Build the docker image yourself:

   ::

     sudo ./dretesteth.sh build

   .. note::
       This is a slow process. It took me about an hour on a GCP **e2-medium**
       instance.






Conclusion
==========
In most cases people don't start their own client from scratch, but
modify an existing client. If the existing client is already configured
to support **retesteth**, you should now be able to run tests on a
modified version to ensure it still conforms to Ethereum specifications.
If you are writing a completely new client, you still need to implement
the RPC calls that **retesteth** uses and to write the appropriate
configuration (**config**, **start.sh**, and **stop.sh**) for it.

There are several actions you might want to do with **retesteth** beyond
testing a new version of an existing client. Here are links to
documentation. Note that it hasn't been updated in a while, so it may
not be accurate.

-  **Add configuration for a new client**. To do this you need to `add
   retesteth support to the client
   itself <https://github.com/ethereum/retesteth/wiki/RPC-Methods>`__
   and `create a new config for
   it <https://github.com/ethereum/retesteth/wiki/Add-client-configuration-to-Retesteth>`__
-  **Test with a new fork of Ethererum**. New forks usually mean new
   opcodes. Therefore, you will need a docker with a new version of
   `lllc <https://lll-docs.readthedocs.io/en/latest/lll_compiler.html>`__.

If you want to write your own tests, read the next tutorial.
