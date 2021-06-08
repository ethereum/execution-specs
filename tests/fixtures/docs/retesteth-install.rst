.. _retesteth_install:

These directions are written using Debian Linux 10 on Google Cloud
Platform, but should work with minor changes on any other version of
Linux running anywhere else with an Internet connection.

#. Install docker. You may need to reboot afterwards to get the latest
   kernel version.

   ::

      sudo apt install -y wget docker docker.io

#. Download the **retesteth** `docker image <http://retesteth.ethdevops.io/>`_. 
   It is a tar file.

#. Load the docker image: 

   ::

      sudo docker load -i dretest*.tar

#. Download the **dretesteth.sh** script. 

   ::

      wget https://raw.githubusercontent.com/ethereum/retesteth/master/dretesteth.sh
      chmod +x dretesteth.sh 

#. Download the tests:

   ::

      git clone --branch develop https://github.com/ethereum/tests.git

#. Run a test. This has two purposes:

   -  Create the **retesteth** configuration directories in
      **~/tests/config**, where you can modify them.
   -  A sanity check (that you can run tests successfully).

   ::

       sudo ./dretesteth.sh -t GeneralStateTests/stExample -- \
        --testpath ~/tests --datadir /tests/config 


   The output should be similar to:

   ::

      Running 1 test case... 
      Running tests using path: /tests
      Active client configurations: 't8ntool ' 
      Running tests for config 'Ethereum GO on StateTool' 
      Test Case "stExample": 
      100% 
      *** No errors detected 
      *** Total Tests Run: 1 


   .. note:: 
       The **/tests** directory is referenced inside the docker container. It is
       the same as the **~/tests** directory outside it.

#. To avoid having to run with **sudo** all the time, add
   `SUID <https://en.wikipedia.org/wiki/Setuid>`__ permissions to the
   **docker** executable. 

   .. warning::
       This opens potential security risks.
       Don't do it on a VM used by multiple people unless you know what you're doing. 

   :: 
   
       sudo chmod +s /usr/bin/docker-lin\* `which docker`


