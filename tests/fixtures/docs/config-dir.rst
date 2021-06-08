.. config_dir:

#################################
The Retesteth Config Directory
#################################

The retesteth **config** directory contains the **retesteth** configuration. If it is
empty **retesteth** creates one with the default values. Every directory under it 
contains either the default configuration, or configuration for a specific 
client (to override the default for that client).

These directories can contain this information:

- **config** this file contains the client configuration, a JSON file with these
  parameters:

  - **name**, the name of the client

  - **socketType**, the type of socket used to communicate with the client. There
    are four supported types: **tcp**, **ipc**, **ipc-debug**, and **transition-tool**.
    The first three are self explanatory. The **transition-tool** "socket" is used
    by **t8ntool**, which runs a separate instance of **evm t8n** for each test.

    You can find more information about the communication between **retesteth**
    and clients in `the retesteth wiki 
    <https://github.com/ethereum/retesteth/wiki/Add-client-configuration-to-Retesteth>`_.

.. _socketAddress:

  - **socketAddress**, the address of the socket, either a list of TCP ports (in 
    the format **<ip>:<port>**), a file for IPC, or an executable to run (for
    **transition-tool**).

  - **initializeTime**, the time to wait for the client to initialize before
    sending it tests.

  - **forks**, the main supported forks.

  - **additionalForks**, additional forks, which are supported but only if they 
    are specified explicitly. For example, if a client's **config** file specifies:

    ::

      "forks" : [
        "EIP158",
        "Byzantium",
        "Constantinople",
        "ConstantinopleFix",
        "Istanbul",
        "Berlin"
      ],
      "additionalForks" : [
        "EIP158ToByzantiumAt5",
        "HomesteadToDaoAt5",
        "ByzantiumToConstantinopleFixAt5"
      ],        

    And the test specifies **>=Byzantium**, it will test these forks:
   
    - Byzantium
    - Constantinople
    - ConstantinopleFix
    - Istanbul
    - Berlin

    But not additional forks such as **ByzantiumToConstantinopleFixAt5**.
    
  - **exceptions**, the exception messages that the client emits for blocks that
    are invalid in various ways. The key is the string used to identify the exception
    in the **expectException** field of invalid block tests. The value is the message
    the client emits.

    .. note::

       The exception is only checked if:

       #. **-\\-filltests** is specified. 

       #. The test is in **BlockchainTests/InvalidBlocks**.

       Otherwise, either
       **retesteth** only checks that an exception occured, not which exception it 
       was (without **-\\-filltests**), or treats any exception as an abort (if the
       test is not for invalid blocks).  


- **start.sh**  the meaning of this script varies depending on the
  method used to communicate with the client.

  - With **tcp** and **ipc** clients the script
    starts the client and possibly provides it with the port or pipe on 
    which it should listen. In both cases it is possible to start multiple clients 
    to run tests in parallel.

    .. note::

       If there is no **start.sh** script at all **retesteth** assumes that it 
       needs to connect to an existing client rather than run its own.

  - With **ipc-debug** clients the script is ignored, because it is assumed that the
    that the client is already running in debug mode.

  - With **transition-tool** clients the script is executed for every test, and the
    program it runs (**evm t8n** in the case of **geth**) communicates with the client
    to execute the test.

- **stop.sh** stop the client.

- In the case of **transition-tool** clients, this directory also contains the 
  script that runs the client for each test. This script's name is specified in the 
  **socketAddress** field. 

  In the case of **t8ntool**, at writing the only client that uses the **transition-tool**
  socket type, this script is **start.sh**. 

- **genesis/<forkname>.json**, this is the genesis config for the client, primarily
  the way to specify for the client what fork it is running. The forkname value is
  matched with the value for the **network:** field in the test file.
  This file is necessary
  because different clients refer to the forks by different names. 

  This file may
  also contain an **accounts** field. This is legacy and can be ignored.

- **genesis/correctMiningReward.json**, a file that includes the mining reward for
  each fork. 


