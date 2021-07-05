# Eth1.0 Specifications

## Description

This repository contains various specification related to the Ethereum 1.0 chain, specifically the [pyspec](/src/eth1spec/spec.py), specifications for [network upgrades](/network-upgrades), and the [JSON RPC API](/json-rpc). 

### Ethereum Protocol Releases

| Version and Code Name | Block No. | Released | Incl EIPs | Specs | Blog |
|-----------------------|-----------|----------|-----------|-------|-------|
| London | TBD | - | [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) <br> [EIP-3238](https://eips.ethereum.org/EIPS/eip-3238) <br> [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198) <br/> [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529) <br/> [EIP-3554](https://eips.ethereum.org/EIPS/eip-3554)| [Specification](https://github.com/ethereum/eth1.0-specs/blob/master/network-upgrades/mainnet-upgrades/london.md) | - |
| Berlin | 12244000 | 04/15/2021 | [EIP-2565](https://eips.ethereum.org/EIPS/eip-2565) <br/> [EIP-2929](https://eips.ethereum.org/EIPS/eip-2929) <br/> [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) <br/> [EIP-2930](https://eips.ethereum.org/EIPS/eip-2930) | ~[HFM-2070](https://eips.ethereum.org/EIPS/eip-2070)~ <br/> [Specification](https://github.com/ethereum/eth1.0-specs/blob/master/network-upgrades/mainnet-upgrades/berlin.md) | [Blog](https://blog.ethereum.org/2021/03/08/ethereum-berlin-upgrade-announcement/) |
| Muir Glacier | 9200000 | 01/02/2020 | [EIP-2384](https://eips.ethereum.org/EIPS/eip-2384) | [HFM-2387](https://eips.ethereum.org/EIPS/eip-2387) | [Blog](https://blog.ethereum.org/2019/12/23/ethereum-muir-glacier-upgrade-announcement/) |
| Istanbul | 9069000 | 12/07/2019 | [EIP-152](https://eips.ethereum.org/EIPS/eip-152) <br/> [EIP-1108](https://eips.ethereum.org/EIPS/eip-1108) <br/> [EIP-1344](https://eips.ethereum.org/EIPS/eip-1344) <br/> [EIP-1884](https://eips.ethereum.org/EIPS/eip-1884) <br/> [EIP-2028](https://eips.ethereum.org/EIPS/eip-2028) <br/> [EIP-2200](https://eips.ethereum.org/EIPS/eip-2200) | [HFM-1679](https://eips.ethereum.org/EIPS/eip-1679) | [Blog](https://blog.ethereum.org/2019/11/20/ethereum-istanbul-upgrade-announcement/)
| St. Petersburg | 7280000 | 02/28/2019 | [EIP-145](https://eips.ethereum.org/EIPS/eip-145) <br/> [EIP-1014](https://eips.ethereum.org/EIPS/eip-1014) <br/> [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052) <br/> [EIP-1234](https://eips.ethereum.org/EIPS/eip-1234) | [HFM-1716](https://github.com/ethereum/EIPs/pull/1716/) | [Blog](https://blog.ethereum.org/2019/02/22/ethereum-constantinople-st-petersburg-upgrade-announcement/) |
| Constantinople | 7280000 | 02/28/2019 | [EIP-145](https://eips.ethereum.org/EIPS/eip-145) <br/> [EIP-1014](https://eips.ethereum.org/EIPS/eip-1014) <br/> [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052) <br/> [EIP-1234](https://eips.ethereum.org/EIPS/eip-1234) <br/> [EIP-1283](https://eips.ethereum.org/EIPS/eip-1283) | [HFM-1013](https://eips.ethereum.org/EIPS/eip-1013) | [Blog](https://blog.ethereum.org/2019/02/22/ethereum-constantinople-st-petersburg-upgrade-announcement/) |
| Byzantium | 4370000 | 10/16/2017 | [EIP-140](https://github.com/ethereum/EIPs/pull/206) <br/> [EIP-658](https://github.com/ethereum/EIPs/pull/658) <br/> [EIP-196](https://github.com/ethereum/EIPs/pull/213) <br/> [EIP-197](https://github.com/ethereum/EIPs/pull/212) <br/> [EIP-198](https://github.com/ethereum/EIPs/pull/198) <br/> [EIP-211](https://github.com/ethereum/EIPs/pull/211) <br/> [EIP-214](https://github.com/ethereum/EIPs/pull/214) <br/> [EIP-100](https://github.com/ethereum/EIPs/issues/100) <br/> [EIP-649](https://github.com/ethereum/EIPs/pull/669) | [HFM-609](https://eips.ethereum.org/EIPS/eip-609) | [Blog](https://blog.ethereum.org/2017/10/12/byzantium-hf-announcement/) | 
| Spurious Dragon | 2675000 | 11/22/2016 | [EIP-155](https://github.com/ethereum/EIPs/issues/155) <br/> [EIP-160](https://github.com/ethereum/EIPs/issues/160) <br/> [EIP-161](https://github.com/ethereum/EIPs/issues/161) <br/> [EIP-170](https://github.com/ethereum/EIPs/issues/170) | [HFM-607](https://eips.ethereum.org/EIPS/eip-607) | [Blog](https://blog.ethereum.org/2016/11/18/hard-fork-no-4-spurious-dragon/) | 
| Tangerine Whistle | 2463000 | 10/18/2016 | [EIP-150](https://eips.ethereum.org/EIPS/eip-150) | [HFM-608](https://eips.ethereum.org/EIPS/eip-608) | [Blog](https://blog.ethereum.org/2016/10/13/announcement-imminent-hard-fork-eip150-gas-cost-changes/) |
| DAO Fork | 1920000 | 07/20/2016 |  | [HFM-779](https://eips.ethereum.org/EIPS/eip-779) | [Blog](https://blog.ethereum.org/2016/07/15/to-fork-or-not-to-fork/) |
| DAO Wars | aborted | aborted |  |  | [Blog](https://blog.ethereum.org/2016/06/24/dao-wars-youre-voice-soft-fork-dilemma/) |
| Homestead | 1150000 | 03/14/2016  | [EIP-2](https://eips.ethereum.org/EIPS/eip-2) <br/> [EIP-7](https://eips.ethereum.org/EIPS/eip-7) <br/> [EIP-8](https://eips.ethereum.org/EIPS/eip-8) | [HFM-606](https://eips.ethereum.org/EIPS/eip-606) | [Blog](https://blog.ethereum.org/2016/02/29/homestead-release/) |
| Frontier Thawing | 200000 | 09/07/2015 | | | [Blog](https://blog.ethereum.org/2015/08/04/the-thawing-frontier/) |
| Frontier | 1 | 07/30/2015 | | | [Blog](https://blog.ethereum.org/2015/07/22/frontier-is-coming-what-to-expect-and-how-to-prepare/) |

## Consensus Specification (work-in-progress)

The consensus specification is a python implementation of Ethereum that prioritizes readability and simplicity. It [will] accompanied by both narrative and API level documentation of the various components written in restructured text and rendered using Sphinx....

 * [Rendered specification](https://quilt.github.io/eth1.0-specs/)

## Usage

The Ethereum specification is maintained as a Python library, for better integration with tooling and testing.

Requires Python 3.7+

### Building

Building the documentation is most easily done through [`tox`](https://tox.readthedocs.io/en/latest/):

```bash
$ tox -e doc
```

The path to the generated HTML will be printed to the console.

#### Live Preview

A live preview of the documentation can be viewed locally on port `8000` with the following command:

```bash
$ tox -e doc-autobuild
```

### Development

Running the tests necessary to merge into the repository requires:

 * Python 3.7.x (not 3.8 or later), and
 * [PyPy 7.3.x](https://www.pypy.org/).

These version ranges are necessary because, at the time of writing, PyPy is only compatible with Python 3.7.

`eth1.0-specs` depends on a submodule that contains common tests that are run across all clients, so we need to clone the repo with the --recursive flag. Example:
```bash
$ git clone --recursive https://github.com/quilt/eth1.0-specs.git
```

Or, if you've already cloned the repository, you can fetch the submodules with:

```bash
$ git submodule update --init --recursive
```

The tests can be run with:
```bash
$ tox
```

The development tools can also be run outside of `tox`, and can automatically reformat the code:

```bash
$ pip install -e .[doc,lint,test]   # Installs eth1spec, and development tools.
$ isort src                         # Organizes imports.
$ black src                         # Formats code.
$ flake8                            # Reports style/spelling/documentation errors.
$ mypy src                          # Verifies type annotations.
$ pytest                            # Runs tests.
```

It is recommended to use a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment) to keep your system Python installation clean.

## Contribution Guidelines

This specification aims to be:

1. **Correct** - Describe the _intended_ behavior of the Ethereum blockchain, and any deviation from that is a bug.
2. **Complete** - Capture the entirety of _consensus critical_ parts of Ethereum.
3. **Accessible** - Prioritize readability, clarity, and plain language over performance and brevity.

### Spelling

Attempt to use descriptive English words (or _very common_ abbreviations) in documentation and identifiers. If necessary, there is a custom dictionary `whitelist.txt`.
