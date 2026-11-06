"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml

@manually-enhanced: Do not overwrite. Each parametrization runs three
operations (`oper1, oper2, oper3` from the calldata) on the same
measurement contract and stores each one's `Op.GAS` cost in slots 0,
1, 2. EIP-8038 reprices state access, so the cost of every measured
operation shifts by the (Amsterdam - Cancun) repricing of whatever
cold/warm account or storage access it performs. The access pattern,
and hence the delta, depends on what the two preceding operations
already warmed, so the deltas are computed by a small simulator
(`_slot_deltas`) that walks the operation triple while tracking the
warm state of the contract-0 account and storage slot 0x100. Each
component is built only from the fork's own gas model
(`COLD_ACCOUNT_ACCESS`, `COLD_STORAGE_ACCESS`, the EIP-8038 extra
`WARM_ACCESS` for code reads, and `Op.SSTORE` metadata costs), so
every delta is exactly 0 pre-EIP-8037 and tracks future parameter
changes. The `far*` operations call contract-1 (which does
`BALANCE(contract-0)`) or contract-2 (which does `SLOAD(0x100)`), so
they contribute the inner access's delta. Do not hardcode the
Amsterdam numbers.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def if_then(
    start: int, condition: Bytecode, body: Bytecode, has_value: bool
) -> Bytecode:
    """
    Build the LLL `(if condition body NOP)` layout at code offset `start`.

    Jump destinations are derived from the code length, so the layout
    holds for any address push width.
    """
    skip = Op.PUSH1[0] if has_value else Op.POP(0)
    head = (
        len(Op.JUMPI(pc=Op.PUSH2[0], condition=condition))
        + len(skip)
        + len(Op.JUMP(pc=Op.PUSH2[0]))
    )
    then = start + head
    end = then + len(Op.JUMPDEST) + len(body)
    code = (
        Op.JUMPI(pc=Op.PUSH2[then], condition=condition)
        + skip
        + Op.JUMP(pc=Op.PUSH2[end])
        + Op.JUMPDEST
        + body
        + Op.JUMPDEST
    )
    return code + Op.POP if has_value else code


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/eip2929Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="nop-nop-nop",
        ),
        pytest.param(
            1,
            0,
            0,
            id="sload-sload-sload",
        ),
        pytest.param(
            2,
            0,
            0,
            id="sstore-sstore-sstore",
        ),
        pytest.param(
            3,
            0,
            0,
            id="addr-addr-addr",
        ),
        pytest.param(
            4,
            0,
            0,
            id="addr-addr-addr",
        ),
        pytest.param(
            5,
            0,
            0,
            id="copy-copy-copy",
        ),
        pytest.param(
            6,
            0,
            0,
            id="addr-addr-addr",
        ),
        pytest.param(
            7,
            0,
            0,
            id="call8-call8-call8",
        ),
        pytest.param(
            8,
            0,
            0,
            id="call8-call8-call8",
        ),
        pytest.param(
            9,
            0,
            0,
            id="call5-call5-call5",
        ),
        pytest.param(
            10,
            0,
            0,
            id="call5-call5-call5",
        ),
        pytest.param(
            11,
            0,
            0,
            id="faraddr-faraddr-faraddr",
        ),
        pytest.param(
            12,
            0,
            0,
            id="farcall8-farcall8-farcall8",
        ),
        pytest.param(
            13,
            0,
            0,
            id="farcall5-farcall5-farcall5",
        ),
        pytest.param(
            14,
            0,
            0,
            id="sload-sstore-sload",
        ),
        pytest.param(
            15,
            0,
            0,
            id="sload-farcall8-farcall5",
        ),
        pytest.param(
            16,
            0,
            0,
            id="sload-sstore-farcall5",
        ),
        pytest.param(
            17,
            0,
            0,
            id="farcall8-sload-farcall5",
        ),
        pytest.param(
            18,
            0,
            0,
            id="farcall5-sload-sstore",
        ),
        pytest.param(
            19,
            0,
            0,
            id="addr-addr-addr",
        ),
        pytest.param(
            20,
            0,
            0,
            id="addr-addr-addr",
        ),
        pytest.param(
            21,
            0,
            0,
            id="addr-addr-addr",
        ),
        pytest.param(
            22,
            0,
            0,
            id="addr-addr-addr",
        ),
        pytest.param(
            23,
            0,
            0,
            id="addr-addr-addr",
        ),
        pytest.param(
            24,
            0,
            0,
            id="addr-addr-addr",
        ),
        pytest.param(
            25,
            0,
            0,
            id="call8-call8-call8",
        ),
        pytest.param(
            26,
            0,
            0,
            id="call8-call8-call8",
        ),
        pytest.param(
            27,
            0,
            0,
            id="call5-call5-call5",
        ),
        pytest.param(
            28,
            0,
            0,
            id="call5-call5-call5",
        ),
        pytest.param(
            29,
            0,
            0,
            id="addr-call8-call8",
        ),
        pytest.param(
            30,
            0,
            0,
            id="addr-call8-call8",
        ),
        pytest.param(
            31,
            0,
            0,
            id="addr-call8-call8",
        ),
        pytest.param(
            32,
            0,
            0,
            id="addr-call8-call8",
        ),
        pytest.param(
            33,
            0,
            0,
            id="addr-call8-call8",
        ),
        pytest.param(
            34,
            0,
            0,
            id="addr-call8-call8",
        ),
        pytest.param(
            35,
            0,
            0,
            id="addr-addr-faraddr",
        ),
        pytest.param(
            36,
            0,
            0,
            id="addr-faraddr-addr",
        ),
        pytest.param(
            37,
            0,
            0,
            id="faraddr-addr-addr",
        ),
    ],
)
def test_eip2929(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    # Source: raw
    # 0x00
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #     @@0x100
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SLOAD(key=0x100) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #      (balance 0xca11)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.BALANCE(address=contract_0) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (def 'oper1 $4)
    #    (def 'oper2 $36)
    #    (def 'oper3 $68)
    #
    #    (def 'NOP 0)
    #    (def 'measurementCost 0x022a)
    #
    #    (def 'gasB4     0x00)
    #    (def 'gasAfter  0x20)
    #    (def 'operation 0x40)
    #
    #    ; Write to the memory so memory allocation won't affect the
    #    ; measurement
    #    [gasB4] (gas)
    #    [gasAfter] (gas)
    #
    #    ; Read addresses so that won't affect the measurement
    #    (balance 0xca1100ca11)
    #    (balance   0xca110100)
    #
    #    (def 'tests {
    #        (if (= @operation 1) @@0x100 NOP) ; SLOAD
    #        (if (= @operation 2) [[0x100]] 5 NOP) ; SSTORE
    #        (if (= @operation 11) (balance 0xca11) NOP) ; BALANCE
    #        (if (= @operation 12) (extcodesize 0xca11) NOP) ; EXTCODESIZE
    #        (if (= @operation 13) (extcodecopy 0xca11 0 0 0) NOP) ; EXTCODECOPY  # noqa: E501
    #        (if (= @operation 14) (extcodehash 0xca11) NOP) ; EXTCODEHASH
    #        (if (= @operation 21) (call 0x1000 0xca11 0 0 0 0 0) NOP) ; CALL
    #        (if (= @operation 22) (callcode 0x1000 0xca11 0 0 0 0 0) NOP) ; CALLCODE  # noqa: E501
    # ... (35 more lines)
    measured = [
        (0x1, Op.SLOAD(key=0x100), True),
        (0x2, Op.SSTORE(key=0x100, value=0x5), False),
        (0xB, Op.BALANCE(address=contract_0), True),
        (0xC, Op.EXTCODESIZE(address=contract_0), True),
        (
            0xD,
            Op.EXTCODECOPY(
                address=contract_0, dest_offset=0, offset=0, size=0
            ),
            False,
        ),
        (0xE, Op.EXTCODEHASH(address=contract_0), True),
        (0x15, Op.CALL(gas=0x1000, address=contract_0), True),
        (0x16, Op.CALLCODE(gas=0x1000, address=contract_0), True),
        (0x17, Op.DELEGATECALL(gas=0x1000, address=contract_0), True),
        (0x18, Op.STATICCALL(gas=0x1000, address=contract_0), True),
        (0x1F, Op.CALL(gas=0x1000, address=contract_1), True),
        (0x20, Op.CALLCODE(gas=0x1000, address=contract_2), True),
        (0x21, Op.DELEGATECALL(gas=0x1000, address=contract_2), True),
    ]
    measurement = (
        Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.MSTORE(offset=0x20, value=Op.GAS)
        + Op.POP(Op.BALANCE(address=contract_1))
        + Op.POP(Op.BALANCE(address=contract_2))
    )
    for slot in range(3):
        measurement += Op.MSTORE(
            offset=0x40, value=Op.CALLDATALOAD(offset=4 + 32 * slot)
        ) + Op.MSTORE(offset=0x0, value=Op.GAS)
        for operation, body, has_value in measured:
            condition = Op.EQ(Op.MLOAD(offset=0x40), operation)
            measurement += if_then(
                len(measurement), condition, body, has_value
            )
        measurement += Op.MSTORE(offset=0x20, value=Op.GAS) + Op.SSTORE(
            key=slot,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x0), Op.MLOAD(offset=0x20)), 0x22A
            ),
        )
    contract_3 = pre.deploy_contract(
        code=measurement + Op.SSTORE(key=0x100, value=0x0) + Op.STOP,
        storage={256: 24743},
        balance=0xBA1A9CE0BA1A9CE,
    )

    # EIP-8038 access-repricing component deltas (each 0 pre-EIP-8037).
    gas_costs = fork.gas_costs()
    eip_active = fork.is_eip_enabled(8037)
    cold_account_delta = (
        gas_costs.COLD_ACCOUNT_ACCESS - Cancun.gas_costs().COLD_ACCOUNT_ACCESS
    )
    cold_storage_delta = (
        gas_costs.COLD_STORAGE_ACCESS - Cancun.gas_costs().COLD_STORAGE_ACCESS
    )
    # EIP-8038 charges an extra warm access for an EXTCODE* code read,
    # on every access (cold adds it on top of the cold account cost,
    # warm pays it as a second warm access).
    extra_code_read = gas_costs.WARM_ACCESS if eip_active else 0
    cold_code_read_delta = cold_account_delta + extra_code_read
    warm_code_read_delta = extra_code_read

    def _sstore_delta(**metadata: int) -> int:
        sstore = Op.SSTORE.with_metadata(**metadata)
        return sstore.gas_cost(fork) - sstore.gas_cost(Cancun)

    # SSTORE 24743 -> 5 (existing nonzero slot changed to a new nonzero
    # value): cold first write vs warm subsequent write.
    cold_sstore_write_delta = _sstore_delta(
        key_warm=False, original_value=1, current_value=1, new_value=2
    )
    warm_sstore_write_delta = _sstore_delta(
        key_warm=True, original_value=1, current_value=1, new_value=2
    )

    # Operation opcodes (from the calldata oper words).
    op_nop, op_sload, op_sstore = 0x0, 0x1, 0x2
    op_balance, op_extsize, op_extcopy, op_exthash = 0xB, 0xC, 0xD, 0xE
    op_call0, op_callcode0, op_deleg0, op_static0 = 0x15, 0x16, 0x17, 0x18
    op_call1, op_callcode2, op_deleg2 = 0x1F, 0x20, 0x21
    account_c0_ops = {
        op_balance,
        op_exthash,
        op_call0,
        op_callcode0,
        op_deleg0,
        op_static0,
    }
    code_read_ops = {op_extsize, op_extcopy}
    inner_sload_ops = {op_sload, op_callcode2, op_deleg2}
    # oper triples per data index, matching tx_data below.
    oper_triples = {
        0: (op_nop, op_nop, op_nop),
        1: (op_sload, op_sload, op_sload),
        2: (op_sstore, op_sstore, op_sstore),
        3: (op_balance, op_balance, op_balance),
        4: (op_extsize, op_extsize, op_extsize),
        5: (op_extcopy, op_extcopy, op_extcopy),
        6: (op_exthash, op_exthash, op_exthash),
        7: (op_call0, op_call0, op_call0),
        8: (op_callcode0, op_callcode0, op_callcode0),
        9: (op_deleg0, op_deleg0, op_deleg0),
        10: (op_static0, op_static0, op_static0),
        11: (op_call1, op_call1, op_call1),
        12: (op_callcode2, op_callcode2, op_callcode2),
        13: (op_deleg2, op_deleg2, op_deleg2),
        14: (op_sload, op_sstore, op_sload),
        15: (op_sload, op_callcode2, op_deleg2),
        16: (op_sload, op_sstore, op_deleg2),
        17: (op_callcode2, op_sload, op_deleg2),
        18: (op_deleg2, op_sload, op_sstore),
        19: (op_balance, op_extsize, op_exthash),
        20: (op_balance, op_exthash, op_extsize),
        21: (op_extsize, op_balance, op_exthash),
        22: (op_extsize, op_exthash, op_balance),
        23: (op_exthash, op_extsize, op_balance),
        24: (op_exthash, op_balance, op_extsize),
        25: (op_call0, op_callcode0, op_call0),
        26: (op_callcode0, op_callcode0, op_call0),
        27: (op_deleg0, op_static0, op_deleg0),
        28: (op_deleg0, op_static0, op_static0),
        29: (op_balance, op_call0, op_callcode0),
        30: (op_extsize, op_call0, op_callcode0),
        31: (op_exthash, op_call0, op_callcode0),
        32: (op_balance, op_callcode0, op_call0),
        33: (op_extsize, op_callcode0, op_call0),
        34: (op_exthash, op_callcode0, op_call0),
        35: (op_balance, op_extsize, op_call1),
        36: (op_balance, op_call1, op_exthash),
        37: (op_call1, op_exthash, op_balance),
    }

    def _slot_deltas(index: int) -> tuple[int, int, int]:
        """
        Return the (slot0, slot1, slot2) EIP-8038 deltas for an index.

        Walk the operation triple, tracking the warm state of the
        contract-0 account and storage slot 0x100 (pre-value 24743),
        and accumulate the (Amsterdam - Cancun) repricing each measured
        operation incurs. The `far*` calls reach a pre-warmed contract
        whose body performs the inner access, so they contribute that
        inner access's delta.
        """
        c0_warm = False
        slot_warm = False
        slot_value = 24743
        out = []
        for op in oper_triples[index]:
            delta = 0
            if op in inner_sload_ops:
                # Direct SLOAD(0x100) or a far call whose body SLOADs it.
                if not slot_warm:
                    delta = cold_storage_delta
                    slot_warm = True
            elif op == op_sstore:
                if slot_value != 5:
                    delta = (
                        cold_sstore_write_delta
                        if not slot_warm
                        else warm_sstore_write_delta
                    )
                    slot_value = 5
                slot_warm = True
            elif op in code_read_ops:
                delta = (
                    cold_code_read_delta
                    if not c0_warm
                    else warm_code_read_delta
                )
                c0_warm = True
            elif op in account_c0_ops or op == op_call1:
                # Account access to contract-0 (CALL1's body BALANCEs it).
                if not c0_warm:
                    delta = cold_account_delta
                    c0_warm = True
            out.append(delta)
        return out[0], out[1], out[2]

    def _expect(index: int, base: tuple[int, int, int]) -> dict:
        """Storage dict with each slot bumped by its EIP-8038 delta."""
        deltas = _slot_deltas(index)
        return {i: base[i] + deltas[i] for i in range(3)}

    # Cancun-era base value of each measured slot, per data index. The
    # per-index EIP-8038 delta is added by `_expect`, so each entry is a
    # single data index (grouped entries with identical Cancun bases can
    # still need different deltas once the access pattern differs).
    base_values: dict[int, tuple[int, int, int]] = {
        1: (2090, 90, 90),
        2: (4991, 91, 91),
        3: (2590, 90, 90),
        4: (2590, 90, 90),
        5: (2597, 97, 97),
        6: (2590, 90, 90),
        7: (2608, 108, 108),
        8: (2608, 108, 108),
        9: (2605, 105, 105),
        10: (2605, 105, 105),
        11: (2711, 211, 211),
        12: (2211, 211, 211),
        13: (2208, 208, 208),
        14: (2090, 2891, 90),
        15: (2090, 211, 208),
        16: (2090, 2891, 208),
        17: (2211, 90, 208),
        18: (2208, 90, 2891),
        19: (2590, 90, 90),
        20: (2590, 90, 90),
        21: (2590, 90, 90),
        22: (2590, 90, 90),
        23: (2590, 90, 90),
        24: (2590, 90, 90),
        25: (2608, 108, 108),
        26: (2608, 108, 108),
        27: (2605, 105, 105),
        28: (2605, 105, 105),
        29: (2590, 108, 108),
        30: (2590, 108, 108),
        31: (2590, 108, 108),
        32: (2590, 108, 108),
        33: (2590, 108, 108),
        34: (2590, 108, 108),
        35: (2590, 90, 211),
        36: (2590, 211, 90),
        37: (2711, 90, 90),
    }

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 0})},
        },
    ]
    for index in sorted(base_values):
        expect_entries_.append(
            {
                "indexes": {"data": [index], "gas": -1, "value": -1},
                "network": [">=Cancun"],
                "result": {
                    contract_3: Account(
                        storage=_expect(index, base_values[index])
                    )
                },
            }
        )

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x2) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0xB) + Hash(0xB) + Hash(0xB),
        Bytes("048071d3") + Hash(0xC) + Hash(0xC) + Hash(0xC),
        Bytes("048071d3") + Hash(0xD) + Hash(0xD) + Hash(0xD),
        Bytes("048071d3") + Hash(0xE) + Hash(0xE) + Hash(0xE),
        Bytes("048071d3") + Hash(0x15) + Hash(0x15) + Hash(0x15),
        Bytes("048071d3") + Hash(0x16) + Hash(0x16) + Hash(0x16),
        Bytes("048071d3") + Hash(0x17) + Hash(0x17) + Hash(0x17),
        Bytes("048071d3") + Hash(0x18) + Hash(0x18) + Hash(0x18),
        Bytes("048071d3") + Hash(0x1F) + Hash(0x1F) + Hash(0x1F),
        Bytes("048071d3") + Hash(0x20) + Hash(0x20) + Hash(0x20),
        Bytes("048071d3") + Hash(0x21) + Hash(0x21) + Hash(0x21),
        Bytes("048071d3") + Hash(0x1) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x1) + Hash(0x20) + Hash(0x21),
        Bytes("048071d3") + Hash(0x1) + Hash(0x2) + Hash(0x21),
        Bytes("048071d3") + Hash(0x20) + Hash(0x1) + Hash(0x21),
        Bytes("048071d3") + Hash(0x21) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0xB) + Hash(0xC) + Hash(0xE),
        Bytes("048071d3") + Hash(0xB) + Hash(0xE) + Hash(0xC),
        Bytes("048071d3") + Hash(0xC) + Hash(0xB) + Hash(0xE),
        Bytes("048071d3") + Hash(0xC) + Hash(0xE) + Hash(0xB),
        Bytes("048071d3") + Hash(0xE) + Hash(0xC) + Hash(0xB),
        Bytes("048071d3") + Hash(0xE) + Hash(0xB) + Hash(0xC),
        Bytes("048071d3") + Hash(0x15) + Hash(0x16) + Hash(0x15),
        Bytes("048071d3") + Hash(0x16) + Hash(0x16) + Hash(0x15),
        Bytes("048071d3") + Hash(0x17) + Hash(0x18) + Hash(0x17),
        Bytes("048071d3") + Hash(0x17) + Hash(0x18) + Hash(0x18),
        Bytes("048071d3") + Hash(0xB) + Hash(0x15) + Hash(0x16),
        Bytes("048071d3") + Hash(0xC) + Hash(0x15) + Hash(0x16),
        Bytes("048071d3") + Hash(0xE) + Hash(0x15) + Hash(0x16),
        Bytes("048071d3") + Hash(0xB) + Hash(0x16) + Hash(0x15),
        Bytes("048071d3") + Hash(0xC) + Hash(0x16) + Hash(0x15),
        Bytes("048071d3") + Hash(0xE) + Hash(0x16) + Hash(0x15),
        Bytes("048071d3") + Hash(0xB) + Hash(0xC) + Hash(0x1F),
        Bytes("048071d3") + Hash(0xB) + Hash(0x1F) + Hash(0xE),
        Bytes("048071d3") + Hash(0x1F) + Hash(0xE) + Hash(0xB),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_3,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
