# EIP-8037: State Creation Gas Cost Increase — Cross-Client Reference

> **Purpose**: Canonical reference for any agent or developer comparing EIP-8037 implementations across clients. Use this to find bugs, discrepancies, and verify correctness against the spec.

**Hierarchy of truth**: EIP Spec > EELS (execution-specs) > Client implementations

### Upstream Versions (verified 2026-03-31)

| Source | Branch / Path | HEAD SHA | Date |
|---|---|---|---|
| EIP Spec | `ethereum/EIPs` `EIPS/eip-8037.md` | `7df0a62ca4` | 2026-03-20 |
| EELS | `ethereum/execution-specs` `eips/amsterdam/eip-8037` | `8e3c9fe055` | local branch |
| Nethermind | `NethermindEth/nethermind` `bal-devnet-3` | `2275710d61` | 2026-03-26 |
| go-ethereum | `ethereum/go-ethereum` `bal-devnet-3` | `0253db6ce5` | 2026-03-26 |
| reth (revm) | `paradigmxyz/reth` `bal-devnet-3` / `bluealloy/revm` @ `0abb42b23` | `96a65ba608` / `0abb42b23a` | 2026-03-30 / 2026-03-25 |

---

## Table of Contents

1. [EIP Specification (Source of Truth)](#1-eip-specification-source-of-truth)
2. [EELS — Execution Specs (Reference Implementation)](#2-eels--execution-specs-reference-implementation)
3. [Nethermind (C#)](#3-nethermind-c)
4. [go-ethereum (Go)](#4-go-ethereum-go)
5. [reth / revm (Rust)](#5-reth--revm-rust)
6. [Cross-Client Comparison Matrix](#6-cross-client-comparison-matrix)
7. [Known Issues and TODOs](#7-known-issues-and-todos)

---

## 1. EIP Specification (Source of Truth)

**Source**: [`ethereum/EIPs/EIPS/eip-8037.md`](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-8037.md)
**Status**: Draft | **Requires**: EIP-2780, EIP-7702, EIP-7825, EIP-8011

### 1.1 Dynamic `cost_per_state_byte`

Targets 100 GiB/year state growth at 50% average gas utilization. Uses quantization (5 significant bits + offset 9578) for stability.

```python
raw = ceil((gas_limit * 2_628_000) / (2 * TARGET_STATE_GROWTH_PER_YEAR))
shifted = raw + CPSB_OFFSET           # CPSB_OFFSET = 9578
shift = max(bit_length(shifted) - CPSB_SIGNIFICANT_BITS, 0)  # CPSB_SIGNIFICANT_BITS = 5
cost_per_state_byte = max(((shifted >> shift) << shift) - CPSB_OFFSET, 1)
```

| Parameter | Value |
|---|---|
| `TARGET_STATE_GROWTH_PER_YEAR` | `100 × 1024³` bytes |
| `CPSB_SIGNIFICANT_BITS` | 5 |
| `CPSB_OFFSET` | 9578 |

| Gas Limit | `cost_per_state_byte` |
|:---------:|:---------------------:|
| 60M | 662 |
| 100M | 1,174 |
| 200M | 2,198 |
| 300M | 3,222 |

### 1.2 Harmonized State Creation Costs

`cpsb` = `cost_per_state_byte`

| Operation | State Gas | Regular Gas | State Bytes | Opcodes Affected |
|---|---|---|---|---|
| New account | `112 × cpsb` | 9,000 (same as `GAS_CALL_VALUE`) | 112 | CREATE, CREATE2, create txs |
| Code deposit | `cpsb` per byte | `6 × ceil(len/32)` (hash cost) | len(code) | CREATE, CREATE2, create txs |
| New account (CALL) | `112 × cpsb` | 0 (already has `GAS_CALL_VALUE`) | 112 | CALL* |
| Storage set (0→nonzero) | `32 × cpsb` | 2,900 (`GAS_STORAGE_UPDATE - GAS_COLD_SLOAD`) | 32 | SSTORE |
| Auth empty account | `112 × cpsb` | 0 (included in base) | 112 | EIP-7702 |
| Auth base cost | `23 × cpsb` | 7,500 | 23 | EIP-7702 |
| SELFDESTRUCT new beneficiary | `112 × cpsb` | 0 (replaces `GAS_SELF_DESTRUCT_NEW_ACCOUNT`) | 112 | SELFDESTRUCT |

### 1.3 Multidimensional Metering (Reservoir Model)

Two gas dimensions: `regular_gas` and `state_gas`.

#### Transaction Initialization

```python
intrinsic_gas = intrinsic_regular_gas + intrinsic_state_gas
execution_gas = tx.gas - intrinsic_gas
regular_gas_budget = TX_MAX_GAS_LIMIT - intrinsic_regular_gas  # TX_MAX_GAS_LIMIT = 16,777,216
gas_left = min(regular_gas_budget, execution_gas)
state_gas_reservoir = execution_gas - gas_left
```

#### Charge Semantics

- **Regular gas**: deducts from `gas_left` only.
- **State gas**: deducts from `state_gas_reservoir` first; when exhausted, spills into `gas_left`.
- **Ordering**: regular gas MUST be charged before state gas. If regular gas OOGs, state gas is not charged.
- **`GAS` opcode**: returns `gas_left` only (excludes reservoir).

#### Child Frame Behavior

- Reservoir is passed **in full** to child frames (no 63/64 rule for state gas).
- **Child success**: remaining `state_gas_reservoir` returned to parent.
- **Child revert/halt**: all state gas (reservoir + spillover) restored to parent's reservoir. Child's `state_gas_used` is NOT accumulated.
- **Exceptional halt**: `gas_left` is zeroed (all regular gas consumed). State gas is preserved.
- **System transactions**: not subject to `TX_MAX_GAS_LIMIT` cap; entire `execution_gas` goes to `gas_left` with `state_gas_reservoir = 0`.

#### Block-Level Accounting

```python
tx_regular_gas = intrinsic_regular_gas + execution_regular_gas_used
tx_state_gas = intrinsic_state_gas + execution_state_gas_used

tx_gas_used = max(tx_gas_used_after_refund, calldata_floor_gas_cost)
block_output.block_regular_gas_used += max(tx_regular_gas, calldata_floor_gas_cost)
block_output.block_state_gas_used += tx_state_gas

# Block validity
gas_used = max(block_regular_gas_used, block_state_gas_used)
assert gas_used <= block.gas_limit
```

#### Transaction Gas Used (post-execution)

```python
tx_gas_used_before_refund = tx.gas - tx_output.gas_left - tx_output.state_gas_reservoir
tx_gas_refund = min(tx_gas_used_before_refund // 5, tx_output.refund_counter)
tx_gas_used_after_refund = tx_gas_used_before_refund - tx_gas_refund
```

### 1.4 SSTORE Refunds

When a slot is restored (0→X→0), `refund_counter` gets:
- State gas: `32 × cpsb`
- Regular gas: `GAS_STORAGE_UPDATE - GAS_COLD_SLOAD - GAS_WARM_ACCESS` (2,800)

Net cost after refund: `GAS_WARM_ACCESS` (100).

### 1.5 Contract Deployment

1. **Start**: charge `GAS_CREATE` (9,000 regular + `112 × cpsb` state)
2. **Initcode**: charge actual execution gas
3. **Success**: charge `cpsb × len(code)` state gas, then `6 × ceil(len/32)` regular gas (hash), then persist code
4. **Failure**: no code deposit or hash charges; account unchanged

### 1.6 EIP-7702 Authorizations

Intrinsic assumes account creation for each auth: `(112 + 23) × cpsb` per authorization. When the target account already exists, the `112 × cpsb` portion is refunded to `state_gas_reservoir` during processing.

### 1.7 Pre-state / Post-state Gas Validation (EIP-7928)

| Cost Parameter | Validation Phase | State Gas | Regular Gas |
|---|---|---|---|
| `GAS_CREATE` | Pre-state | `112 × cpsb` | 9,000 |
| `GAS_CODE_DEPOSIT` | Post-state (on deploy success) | `cpsb × L` | `6 × ceil(L/32)` |
| `GAS_NEW_ACCOUNT` | Post-state (requires account check) | `112 × cpsb` | 0 |
| `GAS_STORAGE_SET` | Post-state (requires reading current) | `32 × cpsb` | 2,900 |

For `SSTORE`, the `GAS_CALL_STIPEND` pre-state check applies to `gas_left` only, excluding the reservoir.

---

## 2. EELS — Execution Specs (Reference Implementation)

**Repo**: `ethereum/execution-specs` | **Branch**: `eips/amsterdam/eip-8037`
**Language**: Python | **Location**: `src/ethereum/forks/amsterdam/`

### 2.1 File Map

| File | Purpose |
|---|---|
| `vm/gas.py` | Constants, `state_gas_per_byte()`, `charge_state_gas()`, `charge_gas()`, `check_gas()` |
| `transactions.py` | `IntrinsicGasCost` dataclass, `calculate_intrinsic_cost()`, `validate_transaction()`, `TX_MAX_GAS_LIMIT` |
| `vm/__init__.py` | `BlockOutput.block_state_gas_used`, `TransactionEnvironment.state_gas_reservoir/intrinsic_state_gas`, `Message.state_gas_reservoir`, `Evm.state_gas_left/state_gas_used/regular_gas_used`, `incorporate_child_on_success/error` |
| `vm/interpreter.py` | `MessageCallOutput` (with state gas fields), `process_create_message()` (code deposit + hash cost), `process_message()` (exceptional halt preserves state gas) |
| `vm/instructions/system.py` | CREATE/CREATE2/CALL/CALLCODE/DELEGATECALL/STATICCALL/SELFDESTRUCT with state gas, `generic_create()`, `generic_call()`, `escrow_subcall_regular_gas()` |
| `vm/instructions/storage.py` | SSTORE with `32 × cpsb` on 0→nonzero, restoration refund includes state gas |
| `vm/eoa_delegation.py` | Authorization state gas (new/existing accounts) |
| `fork.py` | Reservoir initialization, block-level 2D accounting, refund logic |
| `utils/message.py` | `prepare_message()` passes reservoir to initial Message |

### 2.2 Key Constants (`vm/gas.py`)

```python
TARGET_STATE_GROWTH_PER_YEAR = Uint(100 * 1024**3)
BLOCKS_PER_YEAR = Uint(2_628_000)
COST_PER_STATE_BYTE_SIGNIFICANT_BITS = Uint(5)
COST_PER_STATE_BYTE_OFFSET = Uint(9578)

STATE_BYTES_PER_NEW_ACCOUNT = Uint(112)
STATE_BYTES_PER_STORAGE_SET = Uint(32)
STATE_BYTES_PER_AUTH_BASE = Uint(23)

PER_AUTH_BASE_COST = Uint(7500)       # regular gas per authorization
REGULAR_GAS_CREATE = Uint(9000)       # regular gas for CREATE
```

### 2.3 Core Functions

#### `state_gas_per_byte(gas_limit)` — `vm/gas.py:132`

**NOTE**: Currently hardcoded to `1174`. Dynamic formula is commented out pending static test fixes.

```python
def state_gas_per_byte(gas_limit):
    return Uint(1174)
    # Formula (commented out):
    # numerator = gas_limit * BLOCKS_PER_YEAR
    # denominator = Uint(2) * TARGET_STATE_GROWTH_PER_YEAR
    # raw = (numerator + denominator - 1) // denominator
    # shifted = raw + COST_PER_STATE_BYTE_OFFSET
    # shift = max(shifted.bit_length() - COST_PER_STATE_BYTE_SIGNIFICANT_BITS, 0)
    # quantized = (shifted >> shift) << shift
    # return max(quantized - COST_PER_STATE_BYTE_OFFSET, 1)
```

#### `charge_state_gas(evm, amount)` — `vm/gas.py:204`

```python
def charge_state_gas(evm, amount):
    if evm.state_gas_left >= amount:
        evm.state_gas_left -= amount
    elif evm.state_gas_left + evm.gas_left >= amount:
        remainder = amount - evm.state_gas_left
        evm.state_gas_left = Uint(0)
        evm.gas_left -= remainder
    else:
        raise OutOfGasError
    evm.state_gas_used += amount
```

#### `incorporate_child_on_error(evm, child_evm)` — `vm/__init__.py:202`

```python
def incorporate_child_on_error(evm, child_evm):
    evm.gas_left += child_evm.gas_left
    evm.state_gas_left += child_evm.state_gas_used + child_evm.state_gas_left
    evm.regular_gas_used += child_evm.regular_gas_used
```

#### Reservoir Initialization — `fork.py`

```python
execution_gas = tx.gas - intrinsic_gas
regular_gas_budget = TX_MAX_GAS_LIMIT - intrinsic.regular
gas = min(regular_gas_budget, execution_gas)
state_gas_reservoir = Uint(execution_gas - gas)
```

### 2.4 Instruction-Level Details

**CREATE/CREATE2** (`vm/instructions/system.py`):
- Charges `REGULAR_GAS_CREATE + extend_memory.cost + init_code_gas` as regular gas
- Charges `STATE_BYTES_PER_NEW_ACCOUNT × cpsb` as state gas
- `generic_create()` passes full reservoir to child (no 63/64 rule)
- On error: `incorporate_child_on_error` restores state gas to parent

**CALL** (`vm/instructions/system.py`):
- Regular gas: access cost + transfer cost + delegation cost + message call gas
- State gas: `STATE_BYTES_PER_NEW_ACCOUNT × cpsb` only when value > 0 AND target not alive
- Regular gas charged BEFORE state gas (`check_gas` then `charge_gas` then `charge_state_gas`)
- Full reservoir passed to child; on error, state gas restored

**SSTORE** (`vm/instructions/storage.py`):
- `check_gas(evm, GAS_CALL_STIPEND + 1)` — stipend check uses `gas_left` only
- 0→nonzero: `charge_gas(gas_cost)` then `charge_state_gas(32 × cpsb)`
- Restoration refund (0→X→0): `state_gas_storage_set + GAS_STORAGE_UPDATE - GAS_COLD_SLOAD - GAS_WARM_ACCESS`

**Code Deposit** (`vm/interpreter.py:process_create_message`):
- `charge_state_gas(evm, len(code) × cpsb)` — state gas first
- `charge_gas(evm, 6 × ceil(len(code)/32) // 32)` — hash cost as regular gas
- On failure: `restore_tx_state`, zero `gas_left`, preserve state gas

**SELFDESTRUCT** (`vm/instructions/system.py`):
- `charge_gas(evm, gas_cost)` — regular gas first
- Then `charge_state_gas(112 × cpsb)` only if beneficiary not alive AND originator has balance

### 2.5 Test Coverage

All in `tests/amsterdam/eip8037_state_creation_gas_cost_increase/`:

| Test File | What It Covers |
|---|---|
| `test_state_gas_pricing.py` | Dynamic pricing, reservoir charging, spill-to-gas_left, OOG, refund cap |
| `test_state_gas_sstore.py` | 0→nonzero charges, nonzero→nonzero skip, restoration refunds, all tx types |
| `test_state_gas_create.py` | CREATE/CREATE2 account + code deposit, revert, OOG, nested, max initcode |
| `test_state_gas_call.py` | Reservoir passing, revert/halt recovery, spill recovery, nested chains, DELEGATECALL, STATICCALL, GAS opcode |
| `test_state_gas_selfdestruct.py` | New beneficiary, existing beneficiary, zero balance |
| `test_state_gas_set_code.py` | Auth intrinsic scaling, existing refunds, mixed, invalid nonce/chain, duplicates |
| `test_state_gas_delegation_pointer.py` | SSTORE via delegation pointer, direct call baseline |
| `test_state_gas_ordering.py` | Regular-before-state enforcement, OOG reservoir inflation prevention |
| `test_state_gas_fork_transition.py` | Fork boundary activation, TX_MAX_GAS_LIMIT transition |
| `test_state_gas_reservoir.py` | Reservoir allocation, spill vs reservoir sourcing, block 2D validity |
| `test_state_gas_calldata_floor.py` | EIP-7623 floor independence, floor > TX_MAX_GAS_LIMIT validation |
| `test_state_gas_multi_block.py` | Multi-block receipt accounting, coinbase fees, diverse paths |
| `test_eip_mainnet.py` | Mainnet-marked (SSTORE, CREATE, create tx) |

---

## 3. Nethermind (C#)

**Repo**: `NethermindEth/nethermind` | **Branch**: `bal-devnet-3`
**Language**: C# | **Root**: `src/Nethermind/`

### 3.1 Architecture

Nethermind uses **compile-time generic type parameters** (`TEip8037 : struct, IFlag`) for zero-cost feature toggling. When `IsEip8037Enabled` is true, the JIT specializes generics with `OnFlag` (eliminating dead branches at compile time). The `IFlag` interface has `static virtual bool IsActive` — `OnFlag` returns true, `OffFlag` returns false.

Gas accounting is encapsulated in the `EthereumGasPolicy` struct with four fields:
```csharp
public long Value;           // Regular gas budget (gas_left)
public long StateReservoir;  // State gas reservoir
public long StateGasUsed;    // Cumulative state gas consumed
public long StateGasSpill;   // State gas that spilled from gas_left
```

### 3.2 IGasPolicy Interface (`IGasPolicy.cs`)

Key EIP-8037 methods (most have default no-op implementations for pre-8037 compatibility):

| Method | Default (pre-8037) | EIP-8037 Behavior |
|---|---|---|
| `GetStateReservoir()` | returns 0 | Returns `StateReservoir` |
| `GetStateGasUsed()` | returns 0 | Returns `StateGasUsed` |
| `GetStateGasSpill()` | returns 0 | Returns `StateGasSpill` |
| `ConsumeStateGas()` | delegates to `UpdateGas` | Reservoir first, then spill to Value |
| `TryConsumeStateAndRegularGas()` | abstract | Regular FIRST, then state gas |
| `ConsumeStorageWrite<TEip8037, TIsSlotCreation>()` | abstract | SSTORE with split cost |
| `ConsumeNewAccountCreation<TEip8037>()` | abstract | State gas for new account |
| `RefundStateGas()` | delegates to `UpdateGasUp` | Refund to reservoir with floor |
| `RestoreChildStateGas()` | no-op | Restore initial reservoir on child error |
| `RevertRefundToHalt()` | no-op | Undo Refund, apply halt restoration |
| `CreateChildFrameGas()` | `FromLong(childRegularGas)` | Transfers full reservoir to child |
| `ApplyCodeInsertRefunds()` | regular refund only | Refunds state to reservoir, returns 0 regular |
| `AuthorizationListCost()` | `(authCount * 25000, 0)` | `(authCount * 7500, authCount * 158490)` |

### 3.3 File Map

| File | Purpose |
|---|---|
| `Nethermind.Evm/GasPolicy/EthereumGasPolicy.cs` | Core 2D gas struct: reservoir, spillover, charge, refund, child frame, intrinsic |
| `Nethermind.Evm/GasPolicy/IGasPolicy.cs` | Interface with default implementations for pre-8037 compatibility |
| `Nethermind.Core/GasCostOf.cs` | Constants (`CostPerStateByte=1174`, `SSetState=37568`, `CreateState=131488`, etc.) |
| `Nethermind.Core/RefundOf.cs` | `SSetReversedEip8037 = SSetState + SSetRegular - WarmStateRead` (40,368) |
| `Nethermind.Core/Specs/SpecGasCosts.cs` | `RefundFromReversal<TEip8037>()` — conditional refund amount |
| `Nethermind.Core/Specs/IReleaseSpec.cs` | `bool IsEip8037Enabled` flag |
| `Nethermind.Core/Eip7825Constants.cs` | When EIP-8037 active, `GetTxGasLimitCap` returns `long.MaxValue` |
| `Nethermind.Evm/CodeDepositHandler.cs` | Splits code deposit: regular=`6×words`, state=`1174×len` |
| `Nethermind.Evm/Instructions/EvmInstructions.cs` | Dispatch table wiring `OnFlag`/`OffFlag` for TEip8037 |
| `Nethermind.Evm/Instructions/EvmInstructions.Storage.cs` | SSTORE with `ConsumeStorageWrite<TEip8037>` |
| `Nethermind.Evm/Instructions/EvmInstructions.Create.cs` | CREATE with `CreateRegular`/`CreateState` split |
| `Nethermind.Evm/Instructions/EvmInstructions.Call.cs` | CALL with `ConsumeNewAccountCreation<TEip8037>` |
| `Nethermind.Evm/Instructions/EvmInstructions.ControlFlow.cs` | SELFDESTRUCT with `ConsumeNewAccountCreation<TEip8037>` |
| `Nethermind.Evm/VirtualMachine.cs` | Main loop: child frame state gas restore, code deposit failure handling |
| `Nethermind.Evm/TransactionProcessing/TransactionProcessor.cs` | TX processing: intrinsic split, reservoir init, block-level 2D accounting |
| `Nethermind.Evm/TransactionProcessing/GasConsumed.cs` | `GasConsumed(SpentGas, OperationGas, BlockGas, BlockStateGas, MaxUsedGas)` |
| `Nethermind.Blockchain/Tracing/BlockReceiptsTracer.cs` | `GasUsed = max(cumulativeRegular, cumulativeState)` |
| `Nethermind.Specs/Forks/25_Amsterdam.cs` | `IsEip8037Enabled = true` |
| `Nethermind.Evm.Test/Eip8037Tests.cs` | Unit tests for gas policy, code deposit, spill, child frames, halt/revert |

### 3.4 Key Constants (`GasCostOf.cs`)

```
CostPerStateByte    = 1174           (hardcoded for devnet-3)
SSetRegular         = 2,900          (GAS_STORAGE_UPDATE - GAS_COLD_SLOAD)
SSetState           = 37,568         (32 × 1174)
CreateRegular       = 9,000
CreateState         = 131,488        (112 × 1174)
NewAccountState     = 131,488        (112 × 1174)
CodeDepositRegularPerWord = 6
CodeDepositState    = 1,174          (per byte)
PerAuthBaseRegular  = 7,500
PerAuthBaseState    = 27,002         (23 × 1174)
PerEmptyAccountState = 131,488       (112 × 1174)
```

### 3.5 Core Mechanisms

**`ConsumeStateGas`**: Reservoir first, then spill to `Value` (gas_left). Tracks spill in `StateGasSpill`.
```csharp
// 1. If reservoir >= cost: deduct from reservoir, increment StateGasUsed
// 2. Otherwise: drain reservoir to 0, spill (cost - reservoir) from Value.
//    If Value insufficient, return false (OOG). Track spill in StateGasSpill.
```

**`TryConsumeStateAndRegularGas`**: Charges regular gas FIRST, then state gas — prevents reservoir inflation on OOG.

**`CreateChildFrameGas`**: Transfers entire reservoir from parent to child. Parent reservoir becomes 0. Child starts with `StateGasUsed=0`, `StateGasSpill=0`.

**`Refund(parent, child)`** (on success): Merges child's `Value`, `StateReservoir`, `StateGasUsed`, `StateGasSpill` into parent.

**`RestoreChildStateGas(parent, child, initialReservoir)`** (on halt/revert):
```csharp
parentGas.StateReservoir += initialStateReservoir + childGas.StateGasSpill;
parentGas.StateGasSpill += childGas.StateGasSpill;
// Full initial reservoir is returned. Spill gas restored to reservoir because
// state ops are reverted, but gas_left is NOT restored (spill penalty stands).
```

**`RevertRefundToHalt`** (code deposit failure after `Refund` already applied):
```csharp
parentGas.StateReservoir += initialStateReservoir + childGas.StateGasSpill - childGas.StateReservoir;
parentGas.StateGasUsed -= childGas.StateGasUsed;
// Undoes the state portion of Refund and applies halt semantics.
```

**`RefundStateGas`** (e.g., SSTORE clear refund to reservoir):
```csharp
gas.StateReservoir += amount;
long newFloor = Math.Max(0, stateGasFloor - amount);
gas.StateGasUsed = Math.Max(gas.StateGasUsed - amount, newFloor);
// Refunds go to reservoir with a floor based on intrinsic state gas.
```

**`CalculateIntrinsicGas`**: Returns `IntrinsicGas<TGasPolicy>` with `Standard.Value = regularGas`, `Standard.StateReservoir = totalStateCost`, `Standard.StateGasUsed = totalStateCost` (intrinsic state is "already used").

**`CreateAvailableFromIntrinsic`**:
```
executionGas = gasLimit - intrinsicRegular - intrinsicState
maxGasLeft = TX_MAX_GAS_LIMIT (16,777,216) - intrinsicRegular
reservoir = max(0, executionGas - maxGasLeft)  // overflow to reservoir
Result = { Value=executionGas-reservoir, StateReservoir=reservoir, StateGasUsed=intrinsicState, StateGasSpill=0 }
```

**Auth intrinsic state cost per authorization**: `NewAccountState + PerAuthBaseState = 131,488 + 27,002 = 158,490`

### 3.6 Block Accounting

```csharp
// BlockReceiptsTracer tracks (cumulativeRegular, cumulativeState) per tx
Block.Header.GasUsed = Math.Max(cumulativeRegular, cumulativeState);
```

**TransactionProcessor block gas**:
```csharp
long txRegularGas = preRefundGas - intrinsicState - reservoirConsumed - stateGasSpill;
long blockGas = max(txRegularGas, floorGas);
long blockStateGas = GetStateGasUsed(gasAfterExecution);
// GasConsumed(SpentGas, OperationGas, BlockGas, BlockStateGas, MaxUsedGas)
```

---

## 4. go-ethereum (Go)

**Repo**: `ethereum/go-ethereum` | **Branch**: `bal-devnet-3`
**Language**: Go | **Root**: `core/vm/`, `core/`, `params/`

### 4.1 Architecture

go-ethereum uses a **`GasCosts` struct** with `RegularGas` and `StateGas` fields for 2D gas accounting. The `Contract.Gas` field holds the current frame's gas budget as `GasCosts`. State gas spillover is implemented in `GasCosts.Sub()` and `GasCosts.Underflow()`.

### 4.2 File Map

| File | Purpose |
|---|---|
| `core/vm/gascosts.go` | `GasCosts{RegularGas, StateGas}`, `GasUsed{RegularGasUsed, StateGasCharged}`, `Underflow()`, `Sub()` with spillover |
| `params/protocol_params.go` | Constants: `MaxTxGas=16777216`, `CreateGasAmsterdam=9000`, `MaxCodeSizeAmsterdam=32768`, `TxAuthTupleRegularGas=7500`, `AccountCreationSize=112`, `StorageCreationSize=32`, `AuthorizationCreationSize=23` |
| `core/evm.go` | `BlockContext.CostPerGasByte`, `CostPerStateByte()` (hardcoded 1174) |
| `core/vm/evm.go` | EVM struct, Call/Create methods return `GasCosts`/`GasUsed`, `initNewContract()` with state gas code deposit |
| `core/vm/contract.go` | `Contract.Gas GasCosts`, `Contract.GasUsed GasUsed`, `UseGas()`, `RefundGas()` |
| `core/vm/interpreter.go` | Main loop: regular-before-state charging for opcodes with `StateGas > 0` |
| `core/vm/gas_table.go` | `gasCreateEip8037()`, `gasCreate2Eip8037()`, `gasCallIntrinsic8037()`, `gasCall8037()`, `gasSelfdestruct8037()`, `gasSStore8037()` |
| `core/vm/operations_acl.go` | `gasCallEIP8037()`, `makeCallVariantGasCallEIP8037()` |
| `core/vm/eips.go` | `enable8037()` — wires gas functions into Amsterdam instruction set |
| `core/vm/jump_table.go` | `newAmsterdamInstructionSet()` |
| `core/vm/instructions.go` | Call/Create opcodes pass `StateGas` to child, escrow pattern, `RefundGas` with error-aware state gas return |
| `core/vm/common.go` | `CheckMaxInitCodeSize/CheckMaxCodeSize` — Amsterdam sizes (65536/32768) |
| `core/state_transition.go` | `IntrinsicGas()`, `buyGas()`, `execute()` with reservoir init, `applyAuthorization()` with state gas refund |
| `core/gaspool.go` | `cumulativeRegular`/`cumulativeState`, `ReturnGasAmsterdam()`, `Used() = max(regular, state)` |
| `params/config.go` | `AmsterdamTime`, `IsAmsterdam()`, `Rules.IsAmsterdam` |

### 4.3 Key Constants (`params/protocol_params.go`)

```go
MaxTxGas                  = 1 << 24       // 16,777,216 (EIP-7825)
CreateGasAmsterdam        = 9000          // regular gas for CREATE (was 32000)
MaxCodeSizeAmsterdam      = 32768         // increased from 24576
MaxInitCodeSizeAmsterdam  = 65536         // 2 × MaxCodeSizeAmsterdam
TxAuthTupleRegularGas     = 7500          // regular gas per auth
TargetStateGrowthPerYear  = 100 * 1024³
AccountCreationSize       = 112
StorageCreationSize       = 32
AuthorizationCreationSize = 23
```

### 4.4 Core Types (`gascosts.go`)

```go
type GasCosts struct {
    RegularGas uint64
    StateGas   uint64
}

type GasUsed struct {
    RegularGasUsed  uint64
    StateGasCharged uint64
}

// Underflow checks if charge would exceed budget, with spillover.
// Accounts for regular gas already consumed by b.RegularGas before checking spill.
func (g GasCosts) Underflow(b GasCosts) bool {
    if b.RegularGas > g.RegularGas { return true }
    if b.StateGas > g.StateGas {
        spillover := b.StateGas - g.StateGas
        remainingRegular := g.RegularGas - b.RegularGas
        if spillover > remainingRegular { return true }
    }
    return false
}

// Sub deducts charge, implementing spillover
func (g *GasCosts) Sub(b GasCosts) {
    g.RegularGas -= b.RegularGas
    if b.StateGas > g.StateGas {
        diff := b.StateGas - g.StateGas
        g.StateGas = 0
        g.RegularGas -= diff  // spillover deducted from regular
    } else {
        g.StateGas -= b.StateGas
    }
}

// Helper methods
func (g GasCosts) Max() uint64  // returns max(RegularGas, StateGas)
func (g GasCosts) Sum() uint64  // returns RegularGas + StateGas
```

### 4.5 Core Mechanisms

**Interpreter** (`interpreter.go`): When `dynamicCost.StateGas > 0`, charges regular gas first (direct deduction from `contract.Gas.RegularGas`), then state gas via `Underflow`/`Sub`:
```go
if evm.chainRules.IsAmsterdam && dynamicCost.StateGas > 0 {
    if contract.Gas.RegularGas < dynamicCost.RegularGas { return nil, ErrOutOfGas }
    contract.GasUsed.RegularGasUsed += dynamicCost.RegularGas
    contract.Gas.RegularGas -= dynamicCost.RegularGas
    stateOnly := GasCosts{StateGas: dynamicCost.StateGas}
    if contract.Gas.Underflow(stateOnly) { return nil, ErrOutOfGas }
    contract.GasUsed.Add(stateOnly)
    contract.Gas.Sub(stateOnly)
}
```

**SSTORE** (`gas_table.go:gasSStore8037`): 0→nonzero charges `{RegularGas: 2900, StateGas: 32*cpsb}`. Restoration refund: `32*cpsb + 2900 - 100`.

**CREATE** (`gas_table.go:gasCreateEip8037`): `{RegularGas: memGas+initCodeGas, StateGas: 112*cpsb}`. Constant gas = 9000. Checks `MaxInitCodeSizeAmsterdam` (65536).

**CALL** (`operations_acl.go:makeCallVariantGasCallEIP8037`): Regular gas (access + transfer + delegation) charged BEFORE state gas (new account creation). Order:
1. EIP-2929 cold access check (regular gas, charged directly via `UseGas`)
2. Intrinsic cost (memory + transfer) charged directly BEFORE state gas
3. EIP-7702 delegation resolution (regular gas, charged directly)
4. State gas (new account creation) computed and charged AFTER regular
5. 63/64 rule applied to remaining regular gas
6. All direct charges temporarily undone for tracer reporting, returned as aggregate

**Code Deposit** (`evm.go:initNewContract`): Checks max code size BEFORE charging gas (so over-max doesn't consume state gas). Then regular gas `6 × ceil(len/32)` first, then state gas `len × cpsb`.

**Child Frames** (`instructions.go`): All call opcodes pass `GasCosts{RegularGas: gas, StateGas: scope.Contract.Gas.StateGas}` to child. Escrow pattern: `scope.Contract.GasUsed.RegularGasUsed -= gas` (undo parent tracking of forwarded gas).

**`Contract.RefundGas`** (`contract.go`): On error, child's `StateGasCharged` is returned to parent's state reservoir. On success, state gas stays consumed. **Critical**: `c.Gas.StateGas = gas.StateGas` is an **assignment** (not `+=`) — child's remaining state gas replaces parent's (because the full reservoir was passed down).
```go
func (c *Contract) RefundGas(err error, gas GasCosts, gasUsed GasUsed, ...) {
    if err != nil {
        gas.StateGas += gasUsed.StateGasCharged  // return state gas on error
        gasUsed.StateGasCharged = 0
    }
    c.Gas.RegularGas += gas.RegularGas
    c.Gas.StateGas = gas.StateGas  // assignment, not addition
    c.GasUsed.StateGasCharged += gasUsed.StateGasCharged
    c.GasUsed.RegularGasUsed += gasUsed.RegularGasUsed
}
```

**Transaction Processing** (`state_transition.go`):
- `IntrinsicGas`: contract creation = `{Regular: 21000+9000, State: 112*cpsb}`. Auth list = `{Regular: n*7500, State: n*(23+112)*cpsb}`.
- `buyGas`: `limit = min(msg.GasLimit, MaxTxGas)`, `initialGas = {Regular: limit, State: msg.GasLimit - limit}`.
- `execute`: splits remaining execution gas: `regularGas = min(MaxTxGas - gas.Regular, executionGas)`, `stateGas = executionGas - regularGas`.
- Post-execution: `txState = (gas.StateGas - authRefund) + execGasUsed.StateGasCharged`, `txRegular = max(gas.Regular + execGasUsed.RegularGasUsed, floorDataGas)`.

**Block Pool** (`gaspool.go`): Tracks `cumulativeRegular`, `cumulativeState`, `cumulativeUsed` (receipt-level). `Used() = max(cumulativeRegular, cumulativeState)`. `AmsterdamDimensions()` returns `(cumulativeRegular, cumulativeState)`.

**Auth Refund** (`state_transition.go:applyAuthorization`): If authority already exists, refunds `112 × cpsb` state gas directly to `st.gasRemaining.StateGas` (not via refund counter).

---

## 5. reth / revm (Rust)

**Repo**: `paradigmxyz/reth` `bal-devnet-3` (HEAD: `96a65ba608`, 2026-03-30)
**EVM**: `bluealloy/revm` @ `0abb42b23` (2026-03-25, merged from `rakita/state-gas` branch)
**Language**: Rust

### 5.1 Architecture

reth delegates EVM execution to **revm**. EIP-8037 state gas is implemented in revm's `GasTracker` struct (4 `u64` fields + 1 `i64`). The reservoir model is integrated into the interpreter, handler, and frame management layers.

```rust
pub struct GasTracker {
    gas_limit: u64,        // gas limit for the frame
    remaining: u64,        // regular gas left (gas_left)
    reservoir: u64,        // state gas pool, separate from remaining
    state_gas_spent: u64,  // total state gas spent so far
    refunded: i64,         // gas refund counter
}
```

`Gas` wraps `GasTracker` + `MemoryGas`. `ResultGas` carries final results:
```rust
pub struct ResultGas {
    total_gas_spent: u64,   // limit - remaining - reservoir
    state_gas_spent: u64,   // state gas consumed
    refunded: u64,          // refund (capped per EIP-3529)
    floor_gas: u64,         // EIP-7623 floor
}
```

### 5.2 File Map (revm)

| File | Purpose |
|---|---|
| `crates/context/interface/src/cfg/gas.rs` | `GasTracker` struct, `record_state_cost()`, `record_regular_cost()`, `InitialAndFloorGas` with `initial_state_gas` |
| `crates/context/interface/src/cfg/gas_params.rs` | Gas constant table (`CPSB=1174`), `sstore_state_gas()`, `new_account_state_gas()`, `code_deposit_state_gas()`, `create_state_gas()`, `split_eip7702_refund()`, `initial_tx_gas()` |
| `crates/interpreter/src/gas.rs` | `Gas` wrapper, `new_with_regular_gas_and_reservoir()`, `record_state_cost()`, `record_regular_cost()`, `spend_all()` (zeros remaining, leaves reservoir) |
| `crates/interpreter/src/instructions/host.rs` | SSTORE `state_gas!()` for new slot, SELFDESTRUCT `new_account_state_gas()` |
| `crates/interpreter/src/instructions/contract.rs` | CREATE/CREATE2 `create_state_gas()`, CALL variants pass `reservoir` in inputs |
| `crates/interpreter/src/instructions/contract/call_helpers.rs` | `load_account_delegated()` returns `(regular_cost, state_cost)` |
| `crates/interpreter/src/instructions/system.rs` | GAS opcode returns `remaining` only (excludes reservoir) |
| `crates/interpreter/src/instructions/macros.rs` | `state_gas!` macro for state gas charging |
| `crates/handler/src/handler.rs` | `first_frame_input()` reservoir init, `last_frame_result()`, `validate_initial_tx_gas()` |
| `crates/handler/src/frame.rs` | `handle_reservoir_remaining_gas()` (child success/error gas return), `return_create()` (code deposit state gas) |
| `crates/handler/src/post_execution.rs` | `build_result_gas()`, `eip7623_check_gas_floor()`, `reimburse_caller()`, `reward_beneficiary()` |
| `crates/handler/src/pre_execution.rs` | EIP-7702 auth list `split_eip7702_refund()` |
| `crates/context/interface/src/cfg.rs` | `is_amsterdam_eip8037_enabled()`, `tx_gas_limit_cap()` |
| `crates/interpreter/src/interpreter_action/call_inputs.rs` | `CallInputs.reservoir: u64` field |

### 5.2b File Map (reth)

| File | Purpose |
|---|---|
| `crates/evm/evm/src/execute.rs` | Block executor, BAL builder integration |
| `crates/stages/stages/src/stages/execution/mod.rs` | BAL validation: `total_bal_items * ITEM_COST <= gas_limit` |
| `crates/ethereum/consensus/src/validation.rs` | Block gas validation, BAL hash check |

### 5.3 Key Constants (`gas_params.rs`)

```rust
const CPSB: u64 = 1174;  // hardcoded for devnet-3

// Amsterdam gas table overrides:
sstore_set_state_gas         = 32 * CPSB       // = 37,568
new_account_state_gas        = 112 * CPSB      // = 131,488
code_deposit_state_gas       = CPSB             // = 1,174 (per byte)
create_state_gas             = 112 * CPSB      // = 131,488
tx_eip7702_per_auth_state_gas = (112 + 23) * CPSB  // = 158,490
sstore_set_refund            = 32 * CPSB + 2800    // = 40,368

// Regular gas changes:
create / tx_create_cost      = 9,000           // (was 32,000)
code_deposit_cost            = 0               // (moved to state gas)
new_account_cost             = 0               // (moved to state gas)
tx_eip7702_per_empty_account = 7500 + (112+23)*CPSB  // = 165,990 (regular + state combined)
tx_eip7702_auth_refund       = 112 * CPSB      // = 131,488 (for existing accounts)
```

### 5.4 Core Mechanisms

**`GasTracker::record_state_cost(cost)`**: Deducts from `reservoir` first; if `reservoir < cost`, the spill (`cost - reservoir`) is deducted from `remaining`. On OOG, nothing is mutated. Accumulates `state_gas_spent`.

**`GasTracker::record_regular_cost(cost)`**: Only deducts from `remaining`, cannot draw from reservoir.

**`Gas::spend_all()`**: Zeros `remaining` only, leaving `reservoir` intact — preserves state gas on exceptional halt.

**`state_gas!` macro**: Used in instruction implementations to charge state gas:
```rust
macro_rules! state_gas {
    ($interpreter:expr, $gas:expr) => {{
        if !$interpreter.gas.record_state_cost($gas) {
            $interpreter.halt_oog();
            return;
        }
    }};
}
```

**Reservoir Initialization** (`handler.rs:first_frame_input`):
```
execution_gas = tx.gas_limit - intrinsic_regular_gas
regular_gas_cap = min(execution_gas, TX_MAX_GAS_LIMIT - intrinsic_regular_gas)
reservoir = execution_gas - regular_gas_cap
```
Then deducts `initial_state_gas` from reservoir (with deficit spilling to regular gas). EIP-7702 reservoir refund is added back.

**Child Frame Gas** (`frame.rs:handle_reservoir_remaining_gas`):
- **On success**: Parent takes child's final reservoir. Parent accumulates child's `state_gas_spent`.
- **On revert/halt**: ALL state gas returns to parent's reservoir (`child.state_gas_spent() + child.reservoir()`), because state changes are rolled back.

**Code Deposit** (`frame.rs:return_create`):
1. Regular gas: `6 * ceil(len / 32)` (keccak256 hash cost)
2. State gas: `CPSB * len` via `record_state_cost`
3. Pre-Amsterdam `code_deposit_cost` (200/byte) is set to **0** under Amsterdam

**SSTORE** (`instructions/host.rs`): Charges `sstore_state_gas()` (37,568) only for new slot creation (zero→non-zero). The `sstore_state_gas()` function checks `new_values_changes_present() && is_original_eq_present()`.

**CALL** (`instructions/contract/call_helpers.rs`): `load_account_delegated()` returns separate `(regular_cost, state_cost)`. State cost = `new_account_state_gas()` when transferring value to empty account.

**GAS opcode** (`instructions/system.rs`): Returns `gas.remaining()` only, excluding reservoir.

**Auth Refund** (`pre_execution.rs`): `split_eip7702_refund(total)` splits into `(state_refund, regular_refund)`. State portion reduces `initial_state_gas` directly (not subject to refund cap). Regular portion goes through standard 1/5 cap.

**Post-execution** (`post_execution.rs`):
- `total_gas_spent = gas.limit() - gas.remaining() - gas.reservoir()`
- `state_gas = gas.state_gas_spent() + initial_state_gas - eip7702_reservoir_refund`
- Reimburses caller: `remaining + reservoir + refunded` (reservoir is unused state gas)
- Rewards beneficiary: `effective_used = gas.used() - gas.reservoir()` (excludes reservoir)

---

## 6. Cross-Client Comparison Matrix

### 6.1 Constants (at 100M gas limit / devnet-3 hardcoded)

| Constant | EIP Spec | EELS | Nethermind | go-ethereum | reth/revm |
|---|---|---|---|---|---|
| `cost_per_state_byte` | 1,174 | 1,174 (hardcoded) | 1,174 (hardcoded) | 1,174 (hardcoded) | 1,174 (hardcoded) |
| `TX_MAX_GAS_LIMIT` | 16,777,216 | 16,777,216 | 16,777,216 | 16,777,216 | 16,777,216 |
| New account state gas | 131,488 | `112 × cpsb` | 131,488 | `112 × cpsb` | `112 × CPSB` = 131,488 |
| Storage set state gas | 37,568 | `32 × cpsb` | 37,568 | `32 × cpsb` | `32 × CPSB` = 37,568 |
| Auth base state gas | 27,002 | `23 × cpsb` | 27,002 | `23 × cpsb` | part of `(112+23)×CPSB` |
| Auth total state gas (per auth) | 158,490 | `(112+23) × cpsb` | 158,490 | `(112+23) × cpsb` | 158,490 |
| CREATE regular gas | 9,000 | 9,000 | 9,000 | 9,000 | 9,000 |
| Auth regular gas | 7,500 | 7,500 | 7,500 | 7,500 | 7,500 |
| SSTORE regular gas (set) | 2,900 | 2,900 | 2,900 | 2,900 | 2,900 |
| Code deposit state gas | `cpsb/byte` | `cpsb/byte` | `1174/byte` | `cpsb/byte` | `CPSB/byte` |
| Code deposit regular gas | `6/word` | `6 × ceil(L/32) // 32` | `6/word` | `6 × ceil(L/32)` | `6 × ceil(L/32)` |
| SSTORE restoration refund | `32×cpsb + 2800` | `32×cpsb + 2800` | 40,368 | `32*cpsb + 2800` | `32*CPSB + 2800` = 40,368 |
| Max code size | 24,576 | 24,576 | 24,576 | 32,768 | — |
| Max initcode size | 49,152 | 49,152 | 49,152 | 65,536 | — |

### 6.2 Behavioral Comparison

| Behavior | EIP Spec | EELS | Nethermind | go-ethereum | reth/revm |
|---|---|---|---|---|---|
| Reservoir spillover to gas_left | Yes | Yes | Yes | Yes | Yes |
| Regular gas charged before state gas | Yes | Yes | Yes | Yes | Yes |
| Full reservoir to child (no 63/64) | Yes | Yes | Yes | Yes | Yes |
| State gas restored on child error | Yes | Yes | Yes | Yes | Yes |
| State gas preserved on exceptional halt | Yes | Yes | Yes | Yes | Yes (`spend_all` zeros remaining only) |
| GAS opcode excludes reservoir | Yes | Yes | Yes | Yes | Yes |
| Block gasUsed = max(regular, state) | Yes | Yes | Yes | Yes | Yes |
| Auth refund for existing accounts | Yes | Yes | Yes | Yes | Yes (split refund) |
| System txs: reservoir = 0 | Yes | Yes | — | — | — |
| Calldata floor applies to regular only | Yes | Yes | Yes | Yes | Yes |

### 6.3 Known Discrepancies to Investigate

| Item | Details |
|---|---|
| `MaxCodeSize` / `MaxInitCodeSize` | go-ethereum uses 32768/65536 (Amsterdam values) while EELS uses 24576/49152 (pre-Amsterdam). Likely from a separate EIP bundled in Amsterdam — verify which one. |
| Dynamic `cost_per_state_byte` | All clients hardcode 1174 for devnet-3. Need to verify the quantization formula matches when dynamic calculation is restored. |
| Code deposit hash cost | EELS: `GAS_KECCAK256_PER_WORD × ceil32(len) // 32`. Verify Nethermind (`CodeDepositRegularPerWord × words`) and geth (`Keccak256WordGas × words`) compute the same word count. |
| `GasCosts.Sub` order in geth | geth's `Sub()` deducts `RegularGas` FIRST, then handles `StateGas` spillover. EELS `charge_state_gas` only touches state+regular (no separate regular deduction in the same call). Verify the combined effect matches for opcodes that charge both dimensions. |
| Spill tracking | Nethermind explicitly tracks `StateGasSpill` as a separate field. EELS and geth don't track spill separately — it's implicit in the gas_left deduction. Verify `RestoreChildStateGas` semantics match `incorporate_child_on_error`. |
| `RefundGas` assignment vs addition | geth uses `c.Gas.StateGas = gas.StateGas` (assignment) when returning child gas. EELS uses `evm.state_gas_left += child.state_gas_used + child.state_gas_left` (addition). Both should yield the same result since parent's reservoir was zeroed before the child call, but verify edge cases. |
| Auth refund mechanism | geth refunds to `st.gasRemaining.StateGas` directly. EELS refunds to `state_gas_reservoir` during auth processing. Nethermind uses `RefundStateGas` with a floor. Verify the floor semantics and timing match. |
| Code deposit failure: max code size check order | geth checks max code size BEFORE charging gas. EELS charges state gas first, then checks max code size. Different OOG-vs-error behavior on oversized code. |

---

## 7. Known Issues and TODOs

### All Clients
- **Hardcoded `cost_per_state_byte`**: All use 1174 for devnet-3. Dynamic formula needs verification across clients when restored.

### EELS
1. `state_gas_per_byte()` hardcoded — dynamic formula commented out in `vm/gas.py:149-163`
2. 623 ported static test failures from insufficient gas (`EIP8037_PORTED_STATIC_FAILURES.md`)
3. 399 remaining failures after partial fixes (`EIP8037_REMAINING_FAILURES.md`)
4. `scripts/bump_ported_gas.py` automates gas limit bumps for ported tests
5. Spec reference version pending merge (`ethereum/EIPs/pull/11328`)

### Nethermind
- `RevertRefundToHalt` complexity — undoes a prior `Refund` then reapplies as halt. Verify this matches EELS `incorporate_child_on_error` semantics exactly.
- `StateGasSpill` restoration on child revert: spill is added back to reservoir but NOT to `gas_left` — verify this matches the EIP spec's "all state gas restored to parent's reservoir" semantics.
- Auth intrinsic state cost = 158,490 per auth (131,488 + 27,002). Verify this matches geth and EELS.

### go-ethereum
- `MaxCodeSizeAmsterdam = 32768` and `MaxInitCodeSizeAmsterdam = 65536` — differs from EELS. May be from a separate EIP bundled in Amsterdam.
- Code deposit max code size check happens BEFORE gas charging — differs from EELS ordering. Could produce different error types on edge cases.
- `CostPerGasByte` is a `BlockContext` field (per-block, set externally) rather than a protocol constant. Verify the external setter computes the same value.
