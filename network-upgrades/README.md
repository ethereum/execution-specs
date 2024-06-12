# Network Upgrades Specifications

## Description

This folder provides the specifications for the various network upgrades to Ethereum execution layer. It contains specifications for the client integration testnets which are set up during the testing phase of upgrades, for the network upgrades which will be deployed to the Ethereum mainnet, as well as retrospectives/postmortems on network upgrade-related incidents.

In an effort to separate this process from the EIP standardization process, three stages have been devised to move EIPs from specifications to being deployed on the Ethereum mainnet: Considered for Inclusion (CFI), Client Integration Testnets, and Mainnet. Below, we explain the process for EIPs to move through these stages.

## Definitions

**Considered for Inclusion**: Signals that client developers are generally positive towards the idea, and that, assuming it meets all the requirements for mainnet inclusion, it could potentially be included in a network upgrade. This means the EIP may be included in client integration testnets. It is similar to "concept ACK" in other open source projects, and is not sufficient to result in deployment to mainnet.

**Client Integration Testnets**: Short-lived integration testnets which are stood up to test cross-client implementations of certain EIPs. This does not guarantee mainnet deployment, and for some EIPs with small or non-applicable changes, this step may be skipped.

**Mainnet**: Signals that client developers wish to include the EIP into an upgrade to the public Ethereum networks (i.e. testnets such as Goerli, Ropsten and Rinkeby and mainnet).

## Process

### Overview 

![CFI Graph](https://user-images.githubusercontent.com/9390255/114197321-11f4aa80-9907-11eb-9c8b-fe09690f6228.png)

### Preconditions for Consideration

_See [EIP-1](https://eips.ethereum.org/EIPS/eip-1#core-eips) for more context._

* You have vetted your idea and created an EIP by opening a PR against the [ethereum/eips](https://github.com/ethereum/EIPs/pulls) repository;
* The EIP is a "Core" EIP;
* The EIP's status is "Draft" or "Review";
* [Optional, but strongly encouraged] You have socialized your EIP and collected some initial feedback in the `discussions-to` links from your EIP.

### Getting the "Considered for Inclusion" (CFI) Status

For your EIP to obtain the CFI status, it should be discussed on the AllCoreDevs call. To propose this, open an issue against the [`ethereum/pm` repository](https://github.com/ethereum/pm/issues/new) which proposes your EIP's inclusion into a specific network upgrade (i.e. "Proposal to include EIP-XXX in $UPGRADE", [example](https://github.com/ethereum/pm/issues/260)).

Even if your EIP obtains the CFI status, it is likely that client developers will raise specific issues that would need to be addressed prior to mainnet inclusion. It is your responsibility as an EIP champion to see that these issues are addressed and to provide an update when that is done.

### Deploying your EIP to Client Integration Testnets

To test cross-client implementations, your EIP will likely be deployed to short-lived client integration testnet in addition to being tested in the [Ethereum tests suite](https://github.com/ethereum/tests/). As this happens, you will be expected to provide technical input and guidance to client implementers. Providing a full implementation against one or more of the major Ethereum clients is appreciated.

Note: by this point, your EIP should be in `Review` status.

### Deploying your EIP to Mainnet

If client developers reach rough consensus to include your EIP in a network upgrade, it will be added to a spec under the `mainnet-upgrades` folder. When the upgrade spec gets finalized (i.e. the list of EIPs is final and blocks are selected), your EIP should be moved to the `Last Call` status. 
