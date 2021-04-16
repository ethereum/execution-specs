## Purpose

To describe the process of preparing and activating the Berlin network upgrade.

### Upgrade summary 
* Date and time (in UTC): Apr-15-2021 
* Block Number (Mainnet): 10:07:03 AM +UTC
* Mined by: Hiveon Pool
* Block Reward: 2.884653520945903523 Ether (2 + 0.884653520945903523)
* Uncles Reward: 0
* Difficulty: 6,696,239,334,037,736
* Total Difficulty: 23,316,419,380,214,989,812,302
* Block number (Ropsten): 9812189

### EIP Included 

- [EIP-2565: Repricing of the EIP-198 ModExp precompile](https://eips.ethereum.org/EIPS/eip-2565)
- [EIP-2718: Typed Transaction Envelope](https://eips.ethereum.org/EIPS/eip-2718)
- [EIP-2929: Gas cost increases for state access opcodes](https://eips.ethereum.org/EIPS/eip-2929)
- [EIP-2930: Optional access lists](https://eips.ethereum.org/EIPS/eip-2930)

**Process of EIP selection**
Berlin upgrade upgrade was following process decsribed in [Shedding light on the Ethereum Network Upgrade Process](https://medium.com/ethereum-cat-herders/shedding-light-on-the-ethereum-network-upgrade-process-4c6186ed442c).

### Timeline - Backlog check

**OpenEthereum Consensus Failure**
- April 15, 2021 at 7:12 am EST: [Etherscan went down](https://discordapp.com/channels/595666850260713488/745077610685661265/832211783883423754), 
- April 15, 2021 at 7:30 am EST: [Confirmation from OpenEthereum](https://discordapp.com/channels/595666850260713488/745077610685661265/832216373312618508) 
- April 15, 2021 at 8:21 am EST: [War room](https://discordapp.com/channels/595666850260713488/745077610685661265/832229172126547998) set up :)
- April 15, 2021 at 1:48 pm EST: [OpenEthereum v3.2.3 is released](https://discordapp.com/channels/595666850260713488/745077610685661265/832311394178826291)

#### Discovery of problem 


#### Validation of problem


#### Discussion & decision making 


#### Implementation

OpenEthereum made a [release](https://discordapp.com/channels/595666850260713488/745077610685661265/832311394178826291) that fixed consensus problem that was identified.

### Best Practices
- Running tests having mainnet specs.

### Suggested Corrective Action
(Problem and suggestions)
Problem: Client consensus bug
[Suggestion](https://discordapp.com/channels/595666850260713488/745077610685661265/832280444967190559): Client tests must be run against mainnet spec **directly**. Having separate test spec and mainnet spec could be the reson for slippage as fuzzing can't catch this bug.
It probably increase CI time and extra development effort, since it needs to take into consideration of the whole mainnet genesis block, and will probably have to fake block numbers so that it passes the activation block. But it is important because The test spec or the ropsten spec doesn't have non-active precompile definitions.


## Resources
* All Core Dev Discord 
* Etherscan - https://etherscan.io/block/12244000
