# Archetype 17: hardcoded intrinsic transaction cost

**Invariant.** The constant a relayer uses for the intrinsic transaction charge equals
the charge actually levied. Deployed meta-transaction code hardcodes **21,000**, because
the intrinsic charge is deducted before the first opcode runs — `GAS` never sees it and
no opcode reports it.

**Why it is rule-dependent.** EIP-2780 falsifies the constant, and does something subtler
than reducing it: it **decomposes** a flat charge into a shape-dependent one.

```
base_execution_gas = TX_BASE + recipient_execution_gas              transactions.py:777
  recipient_execution_gas = 0                         if tx.to == sender
                          = COLD_ACCOUNT_ACCESS 3000  otherwise
                          + TX_VALUE_COST 6000        if tx.value > 0
                          = CREATE_ACCESS + init_code_cost   if create
TX_BASE  21,000 (frontier) -> 12,000 (Amsterdam)                    vm/gas.py:143
```

**Measured** (`tests/tools/test_intrinsic_shape_probe.py`, CHECKED):

```
fork            value=0    value=1
Berlin..Osaka   21,000     21,000     flat, shape-independent
Amsterdam       15,000     21,000     shape-dependent
```

A hardcoded 21,000 is therefore still exactly right for a **value-bearing** call, and
over-states by **6,000** for a zero-value one — the overwhelmingly common shape (every
ERC-20 transfer, every plain contract call). The relayer over-reimburses by 6,000 gas ×
gasprice on each, and nothing reverts.

**Deployed witnesses.** Any gas-refunding forwarder: a widely deployed smart-account wallet's `execTransaction`
reimbursement path, GSN relay hubs, EIP-4337 paymaster postOp accounting. L4 measured the
adjacent gas-delta meter shape at 252,006 addresses from 2,499 source files (FP 0/18);
the `21000` constant travels with it. The precise per-contract count is **INFERRED** here
— L1/L2 owe the measured figure for the literal `21000`.

**Reproduce**

```bash
cd engine/eels
./.venv/bin/fill ../../wave1/intrinsic_cost --until Amsterdam \
    --output /tmp/ic -q -p no:cacheprovider          # 44 passed
cd ../../patterns && python3 tools/mutate.py -k tx-
```

**Mutation result** (CHECKED) — and note it discriminates the decomposition:

```text
mutation             intrinsic_cost   every other archetype
tx-base-11000        DETECTED(6)      survives     <- moves BOTH arms
tx-value-cost-5000   DETECTED(3)      survives     <- moves ONLY the value-bearing arm
```

**This is one of two archetypes where asserting a raw gas number IS the invariant**, so
SCHEMA §4.1's prohibition does not apply (it says "unless the gas number IS the
invariant"). Do not repair a failure by rebasing the constants — the constants are the
assertion.

**What a failure means.** The intrinsic charge, or its decomposition, changed. Every
deployed gas-refunding relayer is now reimbursing the wrong amount, silently, in whichever
direction the change went.
