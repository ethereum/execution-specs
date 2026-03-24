"""
Consensus issue test produced by fuzz testing team...

Ported from:
tests/static/state_tests/stRandom2/randomStatetest650Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom2/randomStatetest650Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest650(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Consensus issue test produced by fuzz testing team..."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x61EC5E5029A151E121E39AE4D7546D549EA4B130F645F6F650CEEC0416FE27F4
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    pre[sender] = Account(balance=0x3FFFFFFFFFFFFFFF)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x0)
            + Op.MSTORE(offset=0x20, value=0x10000000)
            + Op.MSTORE(offset=0x40, value=0x0)
            + Op.MSTORE8(offset=0x60, value=0xF6)
            + Op.MSTORE8(offset=0x61, value=0x73)
            + Op.MSTORE8(offset=0x62, value=0xA)
            + Op.MSTORE8(offset=0x63, value=0xEF)
            + Op.MSTORE8(offset=0x64, value=0xBF)
            + Op.MSTORE8(offset=0x65, value=0xBD)
            + Op.MSTORE8(offset=0x66, value=0xEF)
            + Op.MSTORE8(offset=0x67, value=0xBF)
            + Op.MSTORE8(offset=0x68, value=0xBD)
            + Op.MSTORE8(offset=0x69, value=0xEF)
            + Op.MSTORE8(offset=0x6A, value=0xBF)
            + Op.MSTORE8(offset=0x6B, value=0xBD)
            + Op.MSTORE8(offset=0x6C, value=0xEF)
            + Op.MSTORE8(offset=0x6D, value=0xBF)
            + Op.MSTORE8(offset=0x6E, value=0xBD)
            + Op.MSTORE8(offset=0x6F, value=0x3)
            + Op.STATICCALL(
                gas=0xD51402,
                address=0x5,
                args_offset=0x0,
                args_size=0x70,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.SSTORE(key=0x5A430010, value=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
        ),
        nonce=0,
        address=Address("0x9d258197de5279a844b4be3d23547ca4233a70bc"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "000000d514029599b459ce6d7f5a430010f6730aefbfbdefbfbdefbfbdefbfbd03000000"  # noqa: E501
            "d514029599b459ce6d7f5a430010f6730aefbfbdefbfbdefbfbdefbfbd03000000d51402"  # noqa: E501
            "9599b459ce6d7f5a430010f6730aefbfbdefbfbdefbfbdefbfbd0300"
        ),
        gas_limit=1200000,
        value=4022320387,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom2/randomStatetest650Filler.json"],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.pre_alloc_mutable
def test_random_statetest650_from_osaka(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Consensus issue test produced by fuzz testing team..."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x61EC5E5029A151E121E39AE4D7546D549EA4B130F645F6F650CEEC0416FE27F4
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    pre[sender] = Account(balance=0x3FFFFFFFFFFFFFFF)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x0)
            + Op.MSTORE(offset=0x20, value=0x10000000)
            + Op.MSTORE(offset=0x40, value=0x0)
            + Op.MSTORE8(offset=0x60, value=0xF6)
            + Op.MSTORE8(offset=0x61, value=0x73)
            + Op.MSTORE8(offset=0x62, value=0xA)
            + Op.MSTORE8(offset=0x63, value=0xEF)
            + Op.MSTORE8(offset=0x64, value=0xBF)
            + Op.MSTORE8(offset=0x65, value=0xBD)
            + Op.MSTORE8(offset=0x66, value=0xEF)
            + Op.MSTORE8(offset=0x67, value=0xBF)
            + Op.MSTORE8(offset=0x68, value=0xBD)
            + Op.MSTORE8(offset=0x69, value=0xEF)
            + Op.MSTORE8(offset=0x6A, value=0xBF)
            + Op.MSTORE8(offset=0x6B, value=0xBD)
            + Op.MSTORE8(offset=0x6C, value=0xEF)
            + Op.MSTORE8(offset=0x6D, value=0xBF)
            + Op.MSTORE8(offset=0x6E, value=0xBD)
            + Op.MSTORE8(offset=0x6F, value=0x3)
            + Op.STATICCALL(
                gas=0xD51402,
                address=0x5,
                args_offset=0x0,
                args_size=0x70,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.SSTORE(key=0x5A430010, value=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.CALL(
                gas=0xD514,
                address=0x7,
                value=0x295,
                args_offset=0x99B4,
                args_size=0x59CE,
                ret_offset=0x5A43,
                ret_size=0x10,
            )
            + Op.MSTORE(
                offset=0x0,
                value=0xBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6730A,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F673,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xAEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010F6,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0x730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A430010,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0xF6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A4300,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A43,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0xC0,
                value=0x10F6730AEFBFBDEFBFBDEFBFBDEFBFBD03000000D514029599B459CE6D7F5A,  # noqa: E501
            )
            + Op.MSTORE8(offset=0xE0, value=0x43)
            + Op.MSTORE8(offset=0xE1, value=0x0)
            + Op.MSTORE8(offset=0xE2, value=0x10)
            + Op.MSTORE8(offset=0xE3, value=0xF6)
            + Op.MSTORE8(offset=0xE4, value=0x73)
            + Op.MSTORE8(offset=0xE5, value=0xA)
            + Op.MSTORE8(offset=0xE6, value=0xEF)
            + Op.MSTORE8(offset=0xE7, value=0xBF)
            + Op.MSTORE8(offset=0xE8, value=0xBD)
            + Op.MSTORE8(offset=0xE9, value=0xEF)
            + Op.MSTORE8(offset=0xEA, value=0xBF)
            + Op.MSTORE8(offset=0xEB, value=0xBD)
            + Op.MSTORE8(offset=0xEC, value=0xEF)
            + Op.MSTORE8(offset=0xED, value=0xBF)
            + Op.MSTORE8(offset=0xEE, value=0xBD)
            + Op.CALL(
                gas=0x2368EF,
                address=0x2,
                value=0xBFBDEFBF,
                args_offset=0x0,
                args_size=0xEF,
                ret_offset=0x0,
                ret_size=0x20,
            )
        ),
        nonce=0,
        address=Address("0x9d258197de5279a844b4be3d23547ca4233a70bc"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "000000d514029599b459ce6d7f5a430010f6730aefbfbdefbfbdefbfbdefbfbd03000000"  # noqa: E501
            "d514029599b459ce6d7f5a430010f6730aefbfbdefbfbdefbfbdefbfbd03000000d51402"  # noqa: E501
            "9599b459ce6d7f5a430010f6730aefbfbdefbfbdefbfbdefbfbd0300"
        ),
        gas_limit=1200000,
        value=4022320387,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
