"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stPreCompiledContracts2/ecrecoverWeirdVFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stPreCompiledContracts2/ecrecoverWeirdVFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            1,
            0,
            0,
            id="good",
        ),
        pytest.param(
            2,
            0,
            0,
            id="good",
        ),
        pytest.param(
            3,
            0,
            0,
            id="good",
        ),
        pytest.param(
            4,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            5,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            6,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            7,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            8,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            9,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            10,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            11,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            12,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            13,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            14,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            15,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            16,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            17,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            18,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            19,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            20,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            21,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            22,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            23,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            24,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            25,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            26,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            27,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            28,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            29,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            30,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            31,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            32,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            33,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            34,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            35,
            0,
            0,
            id="fail",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_ecrecover_weird_v(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0xDE0C95357363DA5C1C5A73BD7C2781CA5C9FECC1014103B5E1D1E990AE8208EC
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: yul
    # berlin
    # {
    #    let ecRecoverAddr := 1
    #
    #    // Call ecRecover
    #
    #    // Not the most efficient code, but it is more readable to see what each parameter means  # noqa: E501
    #    mstore(0x00, calldataload(0x04))    // msgHash
    #    mstore(0x20, calldataload(0x24))    // v
    #    mstore(0x40, calldataload(0x44))    // r
    #    mstore(0x60, calldataload(0x64))    // s
    #    let res := staticcall(gas(), ecRecoverAddr, 0, 0x80, 0x100, 0x100)
    #
    #    // write results
    #    sstore(0, res)
    #    sstore(1, mload(0x100))
    #    sstore(2, mload(0x120))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH2[0x100]
        + Op.DUP1
        + Op.PUSH1[0x80]
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x1]
        + Op.MSTORE(offset=Op.DUP3, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x24))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x44))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x64))
        + Op.GAS
        + Op.SSTORE(key=0x0, value=Op.STATICCALL)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x100))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x120))
        + Op.STOP,
        storage={0: 24743, 1: 24743, 2: 24743},
        nonce=1,
        address=Address(0x9121BB12ADE6BF12796E6007B21A204E05B1BD49),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [
                    0,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                    32,
                    33,
                    34,
                    35,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1, 1: 0, 2: 0})},
        },
        {
            "indexes": {"data": [1, 2, 3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 1,
                        1: 0xB957B0DA344F6A17F0081D63BE7345A860E5B7A2,
                        2: 0,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(
            "917694f90000000000000000000000000000000000000000000000000000000000007e570000000000000000000000000000000000000000000000000000000000007e570000000000000000000000000000000000000000000000000000000000007e570000000000000000000000000000000000000000000000000000000000007e57"  # noqa: E501
        ),
        Bytes(
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001bce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000001c541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f9deaf0dead0600d0f00d00000000000000060a70000000000000f0ad0bad0beef000000000000000000000000000000000000000000000000000000000000001b8a41a35dfd03f28615dc64b7754457691c66bd73f630c7423280282fa431a5be2d40decf11713d564fa2df10dea5eb2adf45455ed309b4c8cc6853e2498323f5"  # noqa: E501
        ),
        Bytes(
            "917694f9daf5a779ae972f972197303d7b574746c7ef83eadac0f2791ad23db92e4c8e53000000000000000000000000000000000000000000000000000000000000002528ef61340bd939bc2195fe537567866003e1a15d3c71ff63e1590620aa63627667cbe9d8997f761aecb703304b3800ccf555c9f3dc64214b297fb1966a3b6d83"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000025ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000026541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002fce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000030541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000039ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000003a541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004dce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000004e541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000023ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000024541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ebce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f9000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000ec541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000004541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000006541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007ce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000008541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000100541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010ffce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000001100541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100ffce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000010100541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000123456ffce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000012345700541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000deadbeef00ffce354e1b07ba96e325aa4851999f07aabcb4471e49f0a0daafed98caab963f0379d9f3993cdd509f1bfba63dbd23dbdff879fb95203a5049f348a95ce8249f3b"  # noqa: E501
        ),
        Bytes(
            "917694f900000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000deadbeef0100541c4ce1565a646ddde26e1b483a88a6500ce15bd24622492f05cdd18b97161d1827e364c15cfa61dab02339904b1e542f3939c6e8d6367d352026e71ffd6af5"  # noqa: E501
        ),
    ]
    tx_gas = [16777216]
    tx_value = [0]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
