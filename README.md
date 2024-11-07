# Ethereum Execution Client Specifications

[![GitPOAP Badge](https://public-api.gitpoap.io/v1/repo/ethereum/execution-specs/badge)](https://www.gitpoap.io/gh/ethereum/execution-specs)

## Description

This repository contains the specifications related to the Ethereum execution client, specifically the [pyspec](/src/ethereum/frontier/fork.py) and specifications for [network upgrades](/network-upgrades). The [JSON-RPC API specification](https://github.com/ethereum/execution-apis) can be found in a separate repository.

### Ethereum Protocol Releases

| Version and Code Name | Block No. | Released | Incl EIPs | Specs | Blog |
|-----------------------|-----------|----------|-----------|-------|-------|
| Cancun | 19426587 | 2024-03-13<br />(1710338135) | [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153) </br> [EIP-4788](https://eips.ethereum.org/EIPS/eip-4788)</br> [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844)</br> [EIP-5656](https://eips.ethereum.org/EIPS/eip-5656)</br> [EIP-6780](https://eips.ethereum.org/EIPS/eip-6780)</br> [EIP-7516](https://eips.ethereum.org/EIPS/eip-7516)| [Specification](https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/cancun.md) | [Blog](https://blog.ethereum.org/2024/02/27/dencun-mainnet-announcement) |
| Shanghai | 17034870 | 2023-04-12<br/>(1681338455) | [EIP-3651](https://eips.ethereum.org/EIPS/eip-3651) <br/> [EIP-3855](https://eips.ethereum.org/EIPS/eip-3855) <br/> [EIP-3860](https://eips.ethereum.org/EIPS/eip-3860) <br/> [EIP-4895](https://eips.ethereum.org/EIPS/eip-4895) | [Specification](https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/shanghai.md) | [Blog](https://blog.ethereum.org/2023/03/28/shapella-mainnet-announcement) |
| Paris | 15537394 | 2022-09-15 | [EIP-3675](https://eips.ethereum.org/EIPS/eip-3675) <br/> [EIP-4399](https://eips.ethereum.org/EIPS/eip-4399) | [Specification](https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/paris.md) | [Blog](https://blog.ethereum.org/2022/08/24/mainnet-merge-announcement) |
| Gray Glacier | 15050000 | 2022-06-30 | [EIP-5133](https://eips.ethereum.org/EIPS/eip-5133) | [Specification](./network-upgrades/mainnet-upgrades/gray-glacier.md) | [Blog](https://blog.ethereum.org/2022/06/16/gray-glacier-announcement/) |
| Arrow Glacier | 13773000 | 2021-12-09 | [EIP-4345](https://eips.ethereum.org/EIPS/eip-4345) | [Specification](./network-upgrades/mainnet-upgrades/arrow-glacier.md) | [Blog](https://blog.ethereum.org/2021/11/10/arrow-glacier-announcement/) |
| London | 12965000 |  2021-08-05 | [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) <br> [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198) <br/> [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529) <br/> [EIP-3541](https://eips.ethereum.org/EIPS/eip-3541) <br> [EIP-3554](https://eips.ethereum.org/EIPS/eip-3554)| [Specification](https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/london.md) | [Blog](https://blog.ethereum.org/2021/07/15/london-mainnet-announcement/) |
| Berlin | 12244000 | 2021-04-15 | [EIP-2565](https://eips.ethereum.org/EIPS/eip-2565) <br/> [EIP-2929](https://eips.ethereum.org/EIPS/eip-2929) <br/> [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) <br/> [EIP-2930](https://eips.ethereum.org/EIPS/eip-2930) | ~[HFM-2070](https://eips.ethereum.org/EIPS/eip-2070)~ <br/> [Specification](https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/berlin.md) | [Blog](https://blog.ethereum.org/2021/03/08/ethereum-berlin-upgrade-announcement/) |
| Muir Glacier | 9200000 | 2020-01-02 | [EIP-2384](https://eips.ethereum.org/EIPS/eip-2384) | [HFM-2387](https://eips.ethereum.org/EIPS/eip-2387) | [Blog](https://blog.ethereum.org/2019/12/23/ethereum-muir-glacier-upgrade-announcement/) |
| Istanbul | 9069000 | 2019-12-07 | [EIP-152](https://eips.ethereum.org/EIPS/eip-152) <br/> [EIP-1108](https://eips.ethereum.org/EIPS/eip-1108) <br/> [EIP-1344](https://eips.ethereum.org/EIPS/eip-1344) <br/> [EIP-1884](https://eips.ethereum.org/EIPS/eip-1884) <br/> [EIP-2028](https://eips.ethereum.org/EIPS/eip-2028) <br/> [EIP-2200](https://eips.ethereum.org/EIPS/eip-2200) | [HFM-1679](https://eips.ethereum.org/EIPS/eip-1679) | [Blog](https://blog.ethereum.org/2019/11/20/ethereum-istanbul-upgrade-announcement/)
| Petersburg | 7280000 | 2019-02-28 | [EIP-145](https://eips.ethereum.org/EIPS/eip-145) <br/> [EIP-1014](https://eips.ethereum.org/EIPS/eip-1014) <br/> [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052) <br/> [EIP-1234](https://eips.ethereum.org/EIPS/eip-1234) | [HFM-1716](https://eips.ethereum.org/EIPS/eip-1716) | [Blog](https://blog.ethereum.org/2019/02/22/ethereum-constantinople-st-petersburg-upgrade-announcement/) |
| Constantinople | 7280000 | 2019-02-28 | [EIP-145](https://eips.ethereum.org/EIPS/eip-145) <br/> [EIP-1014](https://eips.ethereum.org/EIPS/eip-1014) <br/> [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052) <br/> [EIP-1234](https://eips.ethereum.org/EIPS/eip-1234) <br/> [EIP-1283](https://eips.ethereum.org/EIPS/eip-1283) | [HFM-1013](https://eips.ethereum.org/EIPS/eip-1013) | [Blog](https://blog.ethereum.org/2019/02/22/ethereum-constantinople-st-petersburg-upgrade-announcement/) |
| Byzantium | 4370000 | 2017-10-16 | [EIP-100](https://eips.ethereum.org/EIPS/eip-100) <br/> [EIP-140](https://eips.ethereum.org/EIPS/eip-140) <br/> [EIP-196](https://eips.ethereum.org/EIPS/eip-196) <br/> [EIP-197](https://eips.ethereum.org/EIPS/eip-197) <br/> [EIP-198](https://eips.ethereum.org/EIPS/eip-198) <br/> [EIP-211](https://eips.ethereum.org/EIPS/eip-211) <br/> [EIP-214](https://eips.ethereum.org/EIPS/eip-214) <br/> [EIP-649](https://eips.ethereum.org/EIPS/eip-649) <br/> [EIP-658](https://eips.ethereum.org/EIPS/eip-658) | [HFM-609](https://eips.ethereum.org/EIPS/eip-609) | [Blog](https://blog.ethereum.org/2017/10/12/byzantium-hf-announcement/) |
| Spurious Dragon | 2675000 | 2016-11-22 | [EIP-155](https://eips.ethereum.org/EIPS/eip-155) <br/> [EIP-160](https://eips.ethereum.org/EIPS/eip-160) <br/> [EIP-161](https://eips.ethereum.org/EIPS/eip-161) <br/> [EIP-170](https://eips.ethereum.org/EIPS/eip-170) | [HFM-607](https://eips.ethereum.org/EIPS/eip-607) | [Blog](https://blog.ethereum.org/2016/11/18/hard-fork-no-4-spurious-dragon/) |
| Tangerine Whistle | 2463000 | 2016-10-18 | [EIP-150](https://eips.ethereum.org/EIPS/eip-150) | [HFM-608](https://eips.ethereum.org/EIPS/eip-608) | [Blog](https://blog.ethereum.org/2016/10/13/announcement-imminent-hard-fork-eip150-gas-cost-changes/) |
| DAO Fork | 1920000 | 2016-07-20 |  | [HFM-779](https://eips.ethereum.org/EIPS/eip-779) | [Blog](https://blog.ethereum.org/2016/07/15/to-fork-or-not-to-fork/) |
| DAO Wars | aborted | aborted |  |  | [Blog](https://blog.ethereum.org/2016/06/24/dao-wars-youre-voice-soft-fork-dilemma/) |
| Homestead | 1150000 | 2016-03-14 | [EIP-2](https://eips.ethereum.org/EIPS/eip-2) <br/> [EIP-7](https://eips.ethereum.org/EIPS/eip-7) <br/> [EIP-8](https://eips.ethereum.org/EIPS/eip-8) | [HFM-606](https://eips.ethereum.org/EIPS/eip-606) | [Blog](https://blog.ethereum.org/2016/02/29/homestead-release/) |
| Frontier Thawing | 200000 | 2015-09-07 | | | [Blog](https://blog.ethereum.org/2015/08/04/the-thawing-frontier/) |
| Frontier | 1 | 2015-07-30 | | | [Blog](https://blog.ethereum.org/2015/07/22/frontier-is-coming-what-to-expect-and-how-to-prepare/) |

*Note:* Starting with Paris, updates are no longer rolled out based on block numbers. Paris was enabled once proof-of-work Total Difficulty reached 58750000000000000000000. As of Shanghai (at 1681338455), upgrade activation is based on timestamps.

Some clarifications were enabled without protocol releases:

| EIP | Block No. |
|-----|-----------|
| [EIP-2681](https://eips.ethereum.org/EIPS/eip-2681) | 0 |
| [EIP-3607](https://eips.ethereum.org/EIPS/eip-3607) | 0 |
| [EIP-7523](https://eips.ethereum.org/EIPS/eip-7523) | 15537394 |
| [EIP-7610](https://github.com/ethereum/EIPs/pull/8161) | 0 |


## Execution Specification (work-in-progress)

The execution specification is a python implementation of Ethereum that prioritizes readability and simplicity. It will accompanied by both narrative and API level documentation of the various components written in markdown and rendered using docc...

 * [Rendered specification](https://ethereum.github.io/execution-specs/)

## Usage

The Ethereum specification is maintained as a Python library, for better integration with tooling and testing.

Requires Python 3.10+

### Building

Building the documentation is most easily done through [`tox`](https://tox.readthedocs.io/en/latest/):

```bash
$ tox -e doc
```

The path to the generated HTML will be printed to the console.

# License

The Ethereum Execution Layer Specification code is licensed under the [Creative Commons Zero v1.0 Universal](https://github.com/ethereum/execution-specs/blob/master/LICENSE.md).
