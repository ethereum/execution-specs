# Ethereum Execution Client Specifications

## Description

This repository contains the consensus specifications related to the Ethereum execution client, specifically the [pyspec](/src/ethereum/frontier/spec.py) and specifications for [network upgrades](/network-upgrades). The [JSON-RPC API specification](https://github.com/ethereum/execution-apis) can be found in a separate repository.

### Ethereum Protocol Releases

| Version and Code Name | Block No. | Released | Incl EIPs | Specs | Blog |
|-----------------------|-----------|----------|-----------|-------|-------|
| Shanghai | TBD | TBD | TBD| [Specification](https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/shanghai.md) | |
| Paris | TBD | TBD | TBD| [Specification](https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/paris.md) | |
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

Some clarifications were enabled without protocol releases:

| EIP | Block No. |
|-----|-----------|
| [EIP-2681](https://eips.ethereum.org/EIPS/eip-2681) | 0 |
| [EIP-3607](https://eips.ethereum.org/EIPS/eip-3607) | 0 |

## Consensus Specification (work-in-progress)

The consensus specification is a python implementation of Ethereum that prioritizes readability and simplicity. It [will] accompanied by both narrative and API level documentation of the various components written in restructured text and rendered using Sphinx....

 * [Rendered specification](https://ethereum.github.io/execution-specs/)

## Usage

The Ethereum specification is maintained as a Python library, for better integration with tooling and testing.

Requires Python 3.8+

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

 * Python 3.8.x (not 3.9 or later), and
 * [PyPy 7.3.x](https://www.pypy.org/).
 * `geth` installed and present in `$PATH`

These version ranges are necessary because, at the time of writing, PyPy is only compatible with Python 3.7.

`execution-specs` depends on a submodule that contains common tests that are run across all clients, so we need to clone the repo with the --recursive flag. Example:
```bash
$ git clone --recursive https://github.com/ethereum/execution-specs.git
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
$ pip install -e ".[doc,lint,test]" # Installs eth1spec, and development tools.
$ isort src                         # Organizes imports.
$ black src                         # Formats code.
$ flake8                            # Reports style/spelling/documentation errors.
$ mypy src                          # Verifies type annotations.
$ pytest -n 4                       # Runs tests parallelly.
$ pytest -m "not slow"              # Runs tests which execute quickly.
```

It is recommended to use a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment) to keep your system Python installation clean.

If you want you can also use [pre-commit](https://pre-commit.com/) to reformat the code before every commit. You can install `pre-commit` with:
```bash
$ pip install -U pre-commit
$ pre-commit install  # Setup hooks
```

A trace of the EVM execution for any test case can be obtained by providing the `--evm-trace` argument to pytest.
Note: Make sure to run the EVM trace on a small number of tests at a time. The log might otherwise get very big.
Below is an example.

```bash
pytest tests/frontier/test_state_transition.py -k 'test_general_state_tests_new' --evm-trace
```


## Contribution Guidelines

This specification aims to be:

1. **Correct** - Describe the _intended_ behavior of the Ethereum blockchain, and any deviation from that is a bug.
2. **Complete** - Capture the entirety of _consensus critical_ parts of Ethereum.
3. **Accessible** - Prioritize readability, clarity, and plain language over performance and brevity.

### Spelling

Attempt to use descriptive English words (or _very common_ abbreviations) in documentation and identifiers. If necessary, there is a custom dictionary `whitelist.txt`.


## CLI Utilities `ethereum_spec_tools`

### New Fork Tool
This tool can be used to creates the base code for a new fork by using the existing code from a given fork.

The command takes 4 arguments, 2 of which are optional
 * from_fork: The fork name from which the code is to be duplicated. Eg. - "Tangerine Whistle"
 * to_fork: The fork name of the new fork Eg - "Spurious Dragon"
 * from_test (Optional): Name of the from fork within the test fixtures in case it is different from fork name. Eg. - "EIP150"
 * to_test (Optional): Name of the to fork within the test fixtures in case it is different from fork name Eg - "EIP158"

As an example, if one wants to create baseline code for the `Spurious Dragon` fork from the `Tangerine Whistle` one

```bash
ethereum-spec-new-fork --from_fork="Tangerine Whistle" --to_fork="Spurious Dragon" --from_test=EIP150 --to_test=EIP158
```

The following will have to however, be updated manually
 1. The fork number and MAINNET_FORK_BLOCK in __init__.py
 2. Any absolute package imports from other forks eg. in trie.py
 3. Package names under setup.cfg
 4. Add the new fork to the monkey_patch() function in src/ethereum_optimized/__init__.py
 5. Adjust the underline in fork/__init__.py as well as __init__.py, address.py, message.py in fork/utils
