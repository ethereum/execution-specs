# Release Versioning

Releases for the tests library follow [semantic versioning](https://semver.org/):

- Major number updates every time there is a backwards incompatibility for test runners, e.g.
  - New fork rules
  - Backwards-incompatible format changes
- Minor number updates when new tests are added that are backwards compatible
- Patch number updates if an existing test is bugfixed

Here is an example how a follow-up release line could look like:

- v6-alpha - starting to implement EIPs, but not all EIPs are finalized
- v6-beta - all EIPs finalized, but some tests still in progress
- v6.0.0 - all desired coverage for Constantinople tests to be considered "done enough"
- v6.1.0 - more coverage added
- v6.2.0 - more coverage added
- v6.2.1 - bugfix on one of the tests
- v7.0.0 - change in test format output (if backwards incompatible)

# Release Notes

## v7.0.0

This is the last `Ethereum` tests release with a pre-`Berlin` HF state,
so it provides some stable ground to upgrade client test runners against
to be ready for a `Berlin` hardfork integration.

### Tests Added

#### StateTests / BlockchainTests

##### EIP-2200

Added state tests (also as `BlockchainTests`) to validate the 
EIP-1706/[EIP-2200](https://eips.ethereum.org/EIPS/eip-2200) out of gas condition, 
specifically aimed at validating less than or equals to the stipend handling,
see `GeneralStateTests/stSStoreTest/sstore_gasLeft.json` 
PR [#649](https://github.com/ethereum/tests/pull/649)

##### DIV/SDIV/MOD/SDIV by Zero

Added state tests (also as `BlockchainTests`) checking DIV/SDIV/MOD/SDIV by zero,
see `GeneralStateTests/stSolidityTest/ByZero.json`,
PR [#647](https://github.com/ethereum/tests/pull/647)

##### Stack Validity of SWAP

Added tests checking stack validity of SWAP,
see `GeneralStateTests/stStackTests/stackOverflowSWAP.json` and `[..]/stacksanitySWAP.json`,
PR [#647](https://github.com/ethereum/tests/pull/647)

##### EXTCODEHASH Empty Account

Added more EXTCODEHASH state tests (also as `BlockchainTests`) of nonexistent and 
post suicide accounts, see `GeneralStateTests/stExtCodeHash/callToNonExistent.json`, 
`[..]/callToSuicideThenExtcodehash.json` and `[..]/createEmptyThenExtcodehash.json`,
PR [#654](https://github.com/ethereum/tests/pull/654)

##### SELFBALANCE in different Call Types

Added a composite state test (also in `BlockchainTests`) for SELFBALANCE that 
will do all the exisitng test inside of CALL, DELEGATECALL, and CALLCODE calls,
see `GeneralStateTests/stSelfBalance/selfBalanceCallTypes.json`,
PR [#671](https://github.com/ethereum/tests/pull/671)

##### Retesteth Unit Tests

Introduced retesteth unitTests in 
`BlockchainTests/InvalidBlocks/bcExpectSection/filling_unexpectedAccount.json`,
PR [#676](https://github.com/ethereum/tests/pull/676)

#### Difficulty Tests

Added difficulty tests for [EIP-2384](https://eips.ethereum.org/EIPS/eip-2384)
(Muir Glacier Difficulty Bomb Delay),
PR [#662](https://github.com/ethereum/tests/pull/662)

#### Keystore Tests

Added KeyStore test based on MyCrypto file in order to ensure that the generated 
file is compatible with MyCrypto and Metamask,
PR [#665](https://github.com/ethereum/tests/pull/665)

#### RLP Tests

Added RLP invalid tests for insufficient bytes, see `RLPTests/invalidRLPTest.json`,
PR [#614](https://github.com/ethereum/tests/pull/614)

### Test Format Changes

#### BlockChainTests

##### LegacyTests

`BlockChain` tests up to `ConstantinopleFix` (aka `Petersburg`) now also have been
moved to the [LegacyTests/] folder, the main test folders on this release only 
contain the `Istanbul` tests,
PR [#648](https://github.com/ethereum/tests/pull/648)

##### VMTests -> BlockchainTests

`VMTests` have been converted to `BlockchainTests` and can now be found in
`BlockchainTests/ValidBlocks/VMTests/`,
PR [#680](https://github.com/ethereum/tests/pull/680)

##### PostState Correction

On some LegacyTests `postState` has been corrected to `postStateHash`, you can use
this [repo search](https://github.com/ethereum/tests/search?q=postStateHash&unscoped_q=postStateHash)
to see which tests are affected. This might need some adoption of your test runner.

##### InvalidBlockChain Tests: Expected Block Exceptions

Major blockchain test refactoring, and regeneration on geth + retesteth, see 
[files diff](https://github.com/ethereum/tests/pull/672/files)
for an impression on the format changes (`InvalidBlockchainTests`).
PR [#672](https://github.com/ethereum/tests/pull/672)

### Retesteth

- Add Transition genesis retesteth configurations to default geth configs,
  PR [#646](https://github.com/ethereum/tests/pull/646)
- Updated default mining reward config for transition nets in retesteth configs
  to avoid retesteth error when filling the state tests,
  PR [#650](https://github.com/ethereum/tests/pull/650)
- Use additional forks in retesteth configs. Additional forks used in `TransitionTests` 
  and not automatically used in StateTests/BlockchainTests,
  PR [#651](https://github.com/ethereum/tests/pull/651)
- Enable Istanbul in aleth's retesteth configs,
  PR [#656](https://github.com/ethereum/tests/pull/656)
- Fix ripemd160 precompile name in retesteth configs,
  PR [#659](https://github.com/ethereum/tests/pull/659)
- Fix ECADD and ECMUL precompiles in Istanbul retesteth config,
  PR [#660](https://github.com/ethereum/tests/pull/660)
- Add `ChainID` to Istanbul retesteth config,
  PR [#661](https://github.com/ethereum/tests/pull/661)
- Remove retesteth configs, configs are now stored in retesteth repo.
  PR [#666](https://github.com/ethereum/tests/pull/666)

### Test Fixes

- Reduce 50k bytes code in quadratic complexity tests to 20k bytes
  Resolves issue https://github.com/ethereum/tests/issues/657,
  see `GeneralStateTests/stQuadraticComplexityTest/Call[*]KbytesContract[*].json`,
  PR [#658](https://github.com/ethereum/tests/pull/658) and 
  PR [#669](https://github.com/ethereum/tests/pull/669)
- Minor changes to the test filler format around field strictness, affected tests
  `BlockchainTests/InvalidBlocks/bcExpectSection/filling_wrongStorage2.json`,
  `GeneralStateTests/stExtCodeHash/*`, `GeneralStateTests/stRandom/` (3),
  `GeneralStateTests/stReturnDataTest/subcallReturnMoreThenExpected.json`,
  `GeneralStateTests/stStaticCall/static_call_value_inherit.json`,
  `GeneralStateTests/stTransactionTest/Opcodes_TransactionInit.json`,
  PR [#677](https://github.com/ethereum/tests/pull/677)
- Upgrade and regenerate invalid RLP blockchain tests,
  PR [#673](https://github.com/ethereum/tests/pull/673)
- Fix test fillers affected by the CompareStates bug, affected tests
  `BlockchainTests/ValidBlocks/bcStateTests/randomStatetest377.json`,
  `GeneralStateTests/stCallCreateCallCodeTest/Call1024PreCalls.json`,
  `GeneralStateTests/stChangedEIP150/Call1024PreCalls.json`,
  `GeneralStateTests/stCreate2/create2checkFieldsInInitcode.json`,
  `GeneralStateTests/stDelegatecallTestHomestead/Call1024PreCalls.json`,
  `GeneralStateTests/stRandom/randomStatetest349.json`,
  `GeneralStateTests/stRandom2/randomStatetest578.json`,
  `GeneralStateTests/stRefundTest/*`,
  `GeneralStateTests/stStaticCall/*`,
  PR [#678](https://github.com/ethereum/tests/pull/678)
- Fixed blockgaslimit in CALLBlake2f_MaxRouds,
  see `GeneralStateTests/stTimeConsuming/CALLBlake2f_MaxRounds.json`,
  PR [#679](https://github.com/ethereum/tests/pull/679)
- Removed `bcExpectSection` in `BlockchainTests` from public tests,
  PR [#684](https://github.com/ethereum/tests/pull/684)

## v7.0.0-beta.1

This is the first `Ethereum` tests release with broader `Istanbul` support,
see the "Istanbul support" section for a list with relevant PRs.

This release also comes with some structural changes to the test folder layout,
the most important ones being the introduction of a new separate `LegacyTests` 
test suite for state tests up to `Constantinople`, a new sub folder structure
for `BlockchainTests` and a new separate suite `GeneralStateTests/stTimeConsuming/`
for time consuming tests. For further details please have a look at the 
"Test Format Changes" section.

### Istanbul Support

#### EIP Test Support

- [EIP-152](https://github.com/ethereum/EIPs/pull/2129): Blake2b `F` precompile,
  `CALL` and `CALLCODE` tests added for the standard unit test vectors for
  Blake2b `F`,
  PR [#619](https://github.com/ethereum/tests/pull/619)
- [EIP-1344](https://eips.ethereum.org/EIPS/eip-1344): ChainID opcode, state
  tests added in PR [#627](https://github.com/ethereum/tests/pull/627)
- [EIP-1884](https://eips.ethereum.org/EIPS/eip-1884): Repricing for 
  trie-size-dependent opcodes, `SELFBALANCE` and `SLOAD` gas cost tests added
  in PR [#627](https://github.com/ethereum/tests/pull/627)

#### Test Regeneration

- Regeneration of `BlockchainTests/GeneralStateTests` (`hive` tests),
  PR [#632](https://github.com/ethereum/tests/pull/632)
- Updated `TransactionTests/` to `Istanbul`,
  PR [#633](https://github.com/ethereum/tests/pull/633)
- Updated state tests with latest `lllc`,
  PR [#635](https://github.com/ethereum/tests/pull/635)
- Updated `GeneralStateTests` to `Istanbul`,
  PR [#639](https://github.com/ethereum/tests/pull/639)

### Constantinople/Petersburg Updates

The following tests touching Constantinople/Petersburg behavior have been added
or updated since the last release:

- Added `ConstantinopleFix` (aka `Petersburg`) tests,
  PR [#582](https://github.com/ethereum/tests/pull/582)
- Updated `ByzantiumToConstantinople` transition test to
  `ByzantiumToConstantinopleFix`
  (see `BlockchainTests/TransitionTests`),
  PR [#583](https://github.com/ethereum/tests/pull/583),
  PR [#588](https://github.com/ethereum/tests/pull/588)
- New `SAR`, `SHL`, `SHR` combinations,
  PR [#574](https://github.com/ethereum/tests/pull/574)

### Test Format Changes

- New `LegacyTests` suite for `BlockchainTests/GeneralStateTests` and
  `GeneralStateTests` for HFs up to `Constantinople` (so not:
  `ConstantinopleFix` aka `Petersburg`),
  PR [#623](https://github.com/ethereum/tests/pull/623)
- New subfolder structure for `BlockchainTests` with added folders
  for `InvalidBlocks` and `ValidBlocks`,
  PR [#605](https://github.com/ethereum/tests/pull/605)
- New separate suite `GeneralStateTests/stTimeConsuming/` for time
  consuming tests,
  PR [#595](https://github.com/ethereum/tests/pull/595)
- Moved blockchain specific tests from `GeneralStateTests` to
  `BlockchainTests`,
  PR [#590](https://github.com/ethereum/tests/pull/590)
- Old unmaintained RPC test scripts in `RPCTests` have been removed,
  PR [#573](https://github.com/ethereum/tests/pull/573)

### Retesteth / RPC

- Added `Istanbul` to `Retesteth` configuration,
  PR [#638](https://github.com/ethereum/tests/pull/638)
- Updated `Retesteth` configurations,
  PR [#634](https://github.com/ethereum/tests/pull/634)
- Default `Retesteth` genesis configurations,
  PR [#625](https://github.com/ethereum/tests/pull/625)
- Added `Retesteth` configuration for `Pantheon` client,
  PR [#622](https://github.com/ethereum/tests/pull/622)
- Autokill `Geth` threads in `startGethThreads.sh`,
  PR [#613](https://github.com/ethereum/tests/pull/613)
- Added fork configurations to `Geth` config,
  PR [#602](https://github.com/ethereum/tests/pull/602)
- Fixed `BlockchainTests` `RPC` issues,
  PR [#594](https://github.com/ethereum/tests/pull/594)

### General Test Additions

- More `RLP` invalid tests for non-optimal lengths
  (see `RLPTests/`),
  PR [#612](https://github.com/ethereum/tests/pull/612)
- More tests on touching precompiles along `REVERT` usage
  (see `GeneralStateTests/stRevertTest/*Touch*.json`),
  PR [#580](https://github.com/ethereum/tests/pull/580), 
  PR [#610](https://github.com/ethereum/tests/pull/610)
- New `sStore` test with non-zero nonce on collision
  (see `GeneralStateTests/stSStoreTest/InitCollisionNonZeroNonce.json`),
  PR [#578](https://github.com/ethereum/tests/pull/578)

### Bug Fixes/Optimizations

- Corrected tests with a missing `expect` section,
  PR [#624](https://github.com/ethereum/tests/pull/624)
- Refill of all `BlockchainTests/GeneralStateTests/`,
  PR [#621](https://github.com/ethereum/tests/pull/621)
- Removed post sections with no post conditions,
  PR [#618](https://github.com/ethereum/tests/pull/618)
- Corrected huge expect sections in state tests
  (see `stAttackTest/`, 'stQuadraticComplexity/'),
  PR [#617](https://github.com/ethereum/tests/pull/617)
- Compressed huge state data in `bcExploitTest` tests,
  PR [#616](https://github.com/ethereum/tests/pull/616)
- Removed ambiguous test in
  `BlockchainTests/ValidBlocks/bcMultiChainTest/ChainAtoChainB_blockorder2.json`,
  PR [#615](https://github.com/ethereum/tests/pull/615)
- Fixed `RevertPrecompiledTouch` test,
  PR [#609](https://github.com/ethereum/tests/pull/609)
- Converted blockchain specific state tests into `BlockchainTests`,
  PR [#607](https://github.com/ethereum/tests/pull/607)
- Various test fixes,
  PR [#603](https://github.com/ethereum/tests/pull/603)
- Fixes and updates to various state tests,
  PR [#599](https://github.com/ethereum/tests/pull/599)
- Fixed `0x` missing in `transaction` -> `data` in `GeneralStateTests`,
  PR [#598](https://github.com/ethereum/tests/pull/598)
- Removed a test case from `badOpcodes` state tests
  (see `GeneralStateTests/stBadOpcode/`),
  PR [#592](https://github.com/ethereum/tests/pull/592)
- Fixed `gasLimit` issue in `GeneralStateTests`,
  PR [#590](https://github.com/ethereum/tests/pull/590)
- Consistently use `0x` prefixes in `RLPTests`,
  PR [#587](https://github.com/ethereum/tests/pull/587)
- Removed underspecified `lotsOfBranches` test
  (see `BlockchainTests/bcTotalDifficultyTest/lotsOfBranches.json`),
  PR [#579](https://github.com/ethereum/tests/pull/579)
- Changed `gasUsed` to 0 in `genesisBlockHeader` for `dataTx` tests
  (see `BlockchainTests/bcValidBlockTest/dataTx.json` and `dataTx2.json`),
  PR [#577](https://github.com/ethereum/tests/pull/577)

## v6.0.0-beta.3

### Potentially breaking changes

- #547 requires your integration to understand the network `ByzantiumToConstantinopleAt5`, which is analogous to existing pseudo networks such as `FrontierToHomesteadAt5` and `EIP158ToByzantiumAt5`.

- #557 changes the format of the rlp tests, byte strings are now prefixed with "0x"

### [EIP 1234](https://eips.ethereum.org/EIPS/eip-1234)

- #547 added a test for the difficulty changes. This adds the network `ByzantiumToConstantinopleAt5`, which is analogous to existing networks such as `FrontierToHomesteadAt5` and `EIP158ToByzantiumAt5`.

### [EIP 1052](https://eips.ethereum.org/EIPS/eip-1052)

- #548 Added a test for EXTCODEHASH called on an account created in the same transaction
- #549 added a few more tests for EXTCODEHASH and EXTCODESIZE on accounts created in the same transaction
- #550 Checks that changes to an account's nonce, balance, or storage do not change the result of calling EXTCODEHASH
- #552 Added another EXTCODEHASH test, what if it's run on accounts which have self-destructed?
- #563 Another spectacularly detailed test case of EXTCODEHASH involving recursive calls and oog-induced revert
- #566 checks that EXTCODEHASH returns a different result when the code changes
- #568 adds a test for EXTCODEHASH; what if the contract being hashed self destructed while in the middle of a delegate call?
- #569 calls EXTCODEHASH on an empty contract

### Misc

- #551 tests for a Constantinople bug the fuzzer found in geth
- #544 adds an RLP test, [courtesy of the mana team](https://github.com/mana-ethereum/ex_rlp/pull/17)
- #557 changes the format of the rlp tests, byte strings are now prefixed with "0x"
- #561 changed some of the tests. There were some changes to `testeth` which made the previous tests impossible to regenerate. They were refactored but not in a way which should break any client.
- #567 adds a Constantinople test Mana found when they failed to sync with Ropsten

## v6.0.0-beta.2 Release CW 46

### Constantinople Test Updates

- Added initial test cases for ``EXTCODEHASH`` [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052), see PR [#484](https://github.com/ethereum/tests/pull/484)
- More ``EXTCODEHASH`` tests, see PR [#544](https://github.com/ethereum/tests/pull/544)
- New ``SSTORE`` state tests and blockchain tests where an external call is overwriting/colliding with new ``SSTORE`` gas calculation rules, see PR [#535](https://github.com/ethereum/tests/pull/535)

### Test Coverage

- New tests to cover cases where the result of an EVM opcode is written to a specified memory range and the result is shorter than the specified range, see PR [#538](https://github.com/ethereum/tests/pull/538)

### Library Changes

- Added ``.idea`` to ``.gitignore``, see PR [#546](https://github.com/ethereum/tests/pull/546)

### Docs

[Test generation docs](https://ethereum-tests.readthedocs.io/en/latest/generating-tests.html) have been consolidated and integrated in the central ReadTheDocs testing documentation. 

We also updated outdated parts on this doc section (see PR [#539](https://github.com/ethereum/tests/pull/539)), so it should in principle now be possible to follow the guide and end up with a working test creation setup. There might still be some glitches, please let us know or submit a PR on [ethereum/tests](https://github.com/ethereum/tests) to if you stumble over something.

Other changes:

- New list with [clients using the library](https://github.com/ethereum/tests#clients-using-the-library) in README, see PR [#537](https://github.com/ethereum/tests/pull/537)

## v6.0.0-beta.1 Release CW 43

### Constantinople Test Summary

- ``EIP-145`` (Bitwise shifting): Tests for ``SAR``, ``SHL`` and ``SHR`` in [GeneralStateTests/stShift](https://github.com/ethereum/tests/tree/develop/GeneralStateTests/stShift) directory, blockchain tests analogue
- ``EIP-1014`` (``CREATE2``): Various cases covered in [GeneralStateTests/stCreate2](https://github.com/ethereum/tests/tree/develop/GeneralStateTests/stCreate2) directory, blockchain tests analogue
- ``EIP-1052`` (``EXTCODEHASH``): Tests not merged yet, open PR [#484](https://github.com/ethereum/tests/pull/484)
- ``EIP-1283`` (``SSTORE``): Dedicated tests in [GeneralStateTests/stSStoreTest](https://github.com/ethereum/tests/tree/develop/GeneralStateTests/stSStoreTest) directory also covering Ropsten consensus issue cases, blockchain tests analogue, generally refilled state tests with new ``SSTORE`` gas metering rules in PR [#511](https://github.com/ethereum/tests/pull/511)
- ``EIP-1234`` (difficulty): New ``difficultyConstantinople.json`` file and regenerated ``difficultyRopsten.json`` files in the [BasicTests](https://github.com/ethereum/tests/blob/develop/BasicTests/) directory, see PR [#518](https://github.com/ethereum/tests/pull/518)

### Library Changes

Be aware that the format of BlockchainTests recently changed with the introduction of a new field ``sealEngine`` (values: ``NoProof`` | ``Ethash``), see related JSON Schema [change](https://github.com/ethereum/tests/commit/3be71ec3364a01fd4f2cb9b9fd086f3f69f0225c) or BlockchainTest format [docs](https://ethereum-tests.readthedocs.io/en/latest/test_types/blockchain_tests.html) for reference.

This means that you can faster-execute ``NoProof`` based tests skipping block validation. These tests nevertheless doesn't provide reliable values for ``PoW``-based block header fields any more (``mixHash``, ``nonce``), so make sure that you don't rely on the correctness of these values for the tests to pass.
