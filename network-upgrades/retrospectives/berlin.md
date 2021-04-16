## Purpose
To describe the process of preparing, activating and error handling during the Berlin upgrade. 

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
- May 15, 2020: Proposal, decision and initial selection of EIPs for Berlin to spin up an ephemeral testnet YOLO in [ACD 87](https://www.youtube.com/watch?v=bGgzALuyY3w&t=4788s)
- May 19: [Meta EIP-2657](https://eips.ethereum.org/EIPS/eip-2657) created for ephemeral testnet YOLO
- May 29: Selection of EIPs, a decision on the state-test name as Yolo-v1 (and not Berlin) in [ACD 88](https://github.com/ethereum/pm/blob/5198ef636a0f2c443a5c99374563ef285b002b0e/All%20Core%20Devs%20Meetings/Meeting%2088.md#decisions-made)
- June 03: Finalized spec of EIPs for v1, commit hash [added](https://github.com/ethereum/EIPs/pull/2657/commits/fb2a20f2d87a272edf0925f1e347b36644268f9b) to YOLO meta EIP
- June 03: Yolo v-1 deployed with [Geth](https://twitter.com/peter_szilagyi/status/1268123563850170368)
- Jun 10: [Open Ethereum](https://twitter.com/vorot93/status/1270597961014218752) and [Besu](https://github.com/hyperledger/besu/pull/1051) joined the network.
- June 10: [YOLO stopped](https://twitter.com/peter_szilagyi/status/1270824487886426113). It went out of disk.
- June 11, 2020: YOLO is back as [YOLT (You only live twice)](https://twitter.com/peter_szilagyi/status/1270931154267504643)
- June 12, 2020: Restarted at AWS cloud
- June 12, 2020: Proposed EIPs for Yolo v2 in [ACD meeting 89](https://github.com/ethereum/pm/blob/master/All%20Core%20Devs%20Meetings/Meeting%2089.md#3-yolo-testnet-update)
- June 22: [yolov1 sealer/bootnode](https://gitter.im/ethereum/AllCoreDevs?at=5ef07f5cfa0c9221fc5288f9) is up with a new IP
- September 18: yolov2 EIP selection in [ACD 96](https://github.com/ethereum/pm/blob/master/All%20Core%20Devs%20Meetings/Meeting%2096.md#decisions-made)
- October 30, 2020: EIP-2537 is not considered for yolov3, and will be delayed until after the next hardfork, decided in [ACD 99](https://github.com/ethereum/pm/blob/master/All%20Core%20Devs%20Meetings/Meeting%2099.md#decisions-made)
- November 27, 2020: EIP-2930 & EIP-2718 added to Berlin EIPs, decided in [ACD 1010](https://github.com/ethereum/pm/blob/master/All%20Core%20Devs%20Meetings/Meeting%20101.md#summary)
- March 08, 2021: Ethereum Berlin Upgrade [Announcement](https://blog.ethereum.org/2021/03/08/ethereum-berlin-upgrade-announcement/)
- Mar 10, 2021: Ropsten at block #9 812 189	
- Mar 17, 2021: Goerli	at block #4 460 644	
- Mar 24, 2021: Rinkeby	at block #8 290 928	
- Apr 15, 2021: Mainnet	at block #12 244 000

**OpenEthereum Consensus Failure**
- April 15, 2021 at 7:12 am EST: [Etherscan went down](https://discordapp.com/channels/595666850260713488/745077610685661265/832211783883423754)
- April 15, 2021 at 7:30 am EST: [Confirmation from OpenEthereum](https://discordapp.com/channels/595666850260713488/745077610685661265/832216373312618508) 
- April 15, 2021 at 8:21 am EST: [War room](https://discordapp.com/channels/595666850260713488/745077610685661265/832229172126547998) set up 
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
