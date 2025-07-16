# TODO

- [x] Update the [EIP-170](./eip-170.md) contract code size limit of 24KB (`0x6000` bytes) to 48KB (`0xc000` bytes).
- [x] Update the [EIP-3860](./eip-3860.md) contract initcode size limit of 48KB (`0xc000` bytes) to 96KB (`0x18000` bytes).
- [x] The cost for `EXTCODESIZE` is updated to acknowlege the potential for two database reads: once for the account (making it warm) and second for code size if bytecode is marked as cold. Bytecode will not be marked as warm as only codesize is read. In addition to the current pricing scheme defined under [EIP-2929](./eip-2929.md), the instruction will also be subject to the `COLD_SLOAD_COST=2100` if code is cold.
  - [x] `EXTCODESIZE` is charged `COLD_SLOAD_COST` if code is cold
  - [x] Bytecode not marked as warm if only codesize is read
  Confirm w/ Sam or Mario
- [x] Introduce a new cold/warm state for contract code, update corresponding gas costs.
Modify the opcodes so that flat `COLD_SLOAD_COST=2100` and dynamic `EXCESS_CODE_COST= ceil32(excess_code_size(len(code))) * GAS_CODE_LOAD_WORD_COST // 32` gas are added to the access cost if the code is cold. When the code is an [EIP-7702](./eip-7702.md) delegation to another account, if target account code is cold add additional gas should be accounted. Warming of the contract code is subjected to the journaling and can be reverted similar to other state warming in [EIP-2930](./eip-2930.md). Opcodes:
  - [x] COLD_SLOAD_COST increased to 2100
  - [x] EXCESS_CODE_COST gas added to cold access cost
  - [x] Warming is "journaled" like in EIP-2930?
  - [x] When code is delegated to another account that is cold, add COLD_SLOAD_COST
    - system.py
      - `CALL` (349)
      - `CALLCODE`  (441)
      - `DELEGATECALL` (589)
      - `STATICCALL` (663)
    - environment.py
      - `EXTCODECOPY` (364)
- [] If a large contract is the entry point of a transaction, the cost calculated in (2) is charged before the execution and contract code is marked as warm. This fee is not calculated towards the initial gas fee. In case of out-of-gas halt, execution will stop and the balance will not be transferred.
  - [] Cold account and code (Contract not in access list nor accessed prior in the txn)
  Add COLD_SLOAD_COST=2100, EXCESS_CODE_COST, and COLD_ACCOUNT_ACCESS_COST=2600
  - [] Warm account and cold code (Already accessed balance, storage, or included in access list (EIP-2930))
  Add COLD_SLOAD_COST=2100, EXCESS_CODE_COST, and WARM_STORAGE_READ_COST=100
  - [] Warm account and code (Already accessed account code)
  Add WARM_STORAGE_READ_COST=100


