"""
Test CALLCODE and DELEGATECALL to precompiles inside a STATICCALL frame.

Ported from:
state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromTransactionFiller.yml
state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromCalledContractFiller.yml
state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromContractInitializationFiller.yml
state_tests/stStaticFlagEnabled/DelegatecallToPrecompileFromTransactionFiller.yml
state_tests/stStaticFlagEnabled/DelegatecallToPrecompileFromCalledContractFiller.yml
state_tests/stStaticFlagEnabled/DelegatecallToPrecompileFromContractInitializationFiller.yml

@manually-enhanced: Do not overwrite. Six CALLCODE and DELEGATECALL fillers
merged.
"""

from typing import Dict, List, Tuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create2_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SIGNER = Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
FEED = 0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED
DEADBEAF = 0xDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAF
HASH_INPUT = 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000
BN128_POINT = (
    0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,
    0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,
)

# Result labels count in decimal-looking hex, as in the filler: the
# zero-value arm returns a result at 0x0a0000 + label * 0x100 and the
# reader stores it at 0x0a00 + label; the value-1 arm uses 0x0b.
LABELS = [int(str(n), 16) for n in range(21)]
RESULTS_OFFSET = 0x0A0000
RESULTS_SIZE = 0x012020
OUTPUT_OFFSET = 0x2000

# Each precompile case: (address, memory input words, args size,
# ret size, results), where a result is "success", "input" (memory
# word 0), "signer" (ecrecover address and its match flag) or an output
# word index, with its expected value.
PrecompileCase = Tuple[int, Dict[int, int], int, int, List[Tuple[str, int]]]
PRECOMPILE_CASES: List[PrecompileCase] = [
    (
        0x1,
        {
            0x00: 0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C,  # noqa: E501
            0x20: 28,
            0x40: 0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F,  # noqa: E501
            0x60: 0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549,  # noqa: E501
        },
        0x80,
        0x20,
        [("success", 1), ("signer", int.from_bytes(SIGNER)), ("match", 1)],
    ),
    (
        0x2,
        {0x00: HASH_INPUT},
        0x20,
        0x20,
        [
            ("success", 1),
            ("input", HASH_INPUT),
            (
                "0",
                0x73F5062FB68ED2A1EC82FF8C73F9251BB9CF53A623BC93527E16BC5AE29DAD74,  # noqa: E501
            ),
        ],
    ),
    (
        0x3,
        {0x00: HASH_INPUT},
        0x20,
        0x20,
        [
            ("success", 1),
            ("input", HASH_INPUT),
            ("0", 0x14EF238CFA4075E9EDE92F18B1566C1DD0B99AAA),
        ],
    ),
    (
        0x4,
        {0x00: HASH_INPUT},
        0x20,
        0x20,
        [("success", 1), ("0", HASH_INPUT)],
    ),
    (
        0x5,
        {
            0x00: 1,
            0x20: 0x20,
            0x40: 0x20,
            0x60: 0x3FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC,  # noqa: E501
            0x80: 0x2EFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC,  # noqa: E501
            0xA0: 0x2F00000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
        },
        0xA1,
        0x20,
        [("success", 1), ("0", 1)],
    ),
    (
        0x6,
        {
            0x00: 0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2,  # noqa: E501
            0x20: 0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA,  # noqa: E501
            0x40: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
            0x60: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
        },
        0x80,
        0x40,
        [("success", 1), ("0", BN128_POINT[0]), ("1", BN128_POINT[1])],
    ),
    (
        0x7,
        {
            0x00: 0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2,  # noqa: E501
            0x20: 0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA,  # noqa: E501
            0x40: 3,
        },
        0x60,
        0x40,
        [("success", 1), ("0", BN128_POINT[0]), ("1", BN128_POINT[1])],
    ),
    (
        0x8,
        {
            0x000: 0x1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59,  # noqa: E501
            0x020: 0x3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41,  # noqa: E501
            0x040: 0x209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7,  # noqa: E501
            0x060: 0x4BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678,  # noqa: E501
            0x080: 0x2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D,  # noqa: E501
            0x0A0: 0x120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550,  # noqa: E501
            0x0C0: 0x111E129F1CF1097710D41C4AC70FCDFA5BA2023C6FF1CBEAC322DE49D1B6DF7C,  # noqa: E501
            0x0E0: 0x2032C61A830E3C17286DE9462BF242FCA2883585B93870A73853FACE6A6BF411,  # noqa: E501
            0x100: 0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,  # noqa: E501
            0x120: 0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,  # noqa: E501
            0x140: 0x90689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,  # noqa: E501
            0x160: 0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,  # noqa: E501
        },
        0x180,
        0x20,
        [("success", 1), ("0", 1)],
    ),
]


def precompile_caller(opcode: Op) -> Tuple[Bytecode, Dict[int, int]]:
    """
    Return code calling every precompile with `opcode`, and its results.

    The code returns the results region; the dict maps each storage key
    the reader copies a result to onto its expected value.
    """
    values = [0, 1] if opcode == Op.CALLCODE else [None]
    code = Bytecode()
    expected: Dict[int, int] = {}
    output = OUTPUT_OFFSET
    for arm, value in enumerate(values):
        label_index = 0
        for address, inputs, args_size, ret_size, results in PRECOMPILE_CASES:
            for offset, word in inputs.items():
                code += Op.MSTORE(offset, word)
            if value is None:
                call = opcode(
                    address=address,
                    args_size=args_size,
                    ret_offset=output,
                    ret_size=ret_size,
                )
            else:
                call = opcode(
                    address=address,
                    value=value,
                    args_size=args_size,
                    ret_offset=output,
                    ret_size=ret_size,
                )
            recovered = Op.MOD(Op.MLOAD(output), Op.EXP(2, 160))
            for kind, expected_value in results:
                label = LABELS[label_index]
                label_index += 1
                memory = RESULTS_OFFSET + arm * 0x10000 + label * 0x100
                if kind == "success":
                    result = call
                elif kind == "signer":
                    result = recovered
                elif kind == "match":
                    result = Op.EQ(SIGNER, recovered)
                elif kind == "input":
                    result = Op.MLOAD(0)
                else:
                    result = Op.MLOAD(output + int(kind) * 0x20)
                code += Op.MSTORE(memory, result)
                expected[0x0A00 + arm * 0x100 + label] = expected_value
            output += 0x40
    code += Op.RETURN(RESULTS_OFFSET, RESULTS_SIZE)
    return code, expected


def results_reader(precompile_caller: Address, keys: List[int]) -> Bytecode:
    """Return code that STATICCALLs the caller and stores its results."""
    code = (
        Op.SSTORE(0, FEED)
        + Op.POP(
            Op.STATICCALL(
                address=precompile_caller,
                ret_offset=RESULTS_OFFSET,
                ret_size=RESULTS_SIZE,
            )
        )
        + Op.SSTORE(1, FEED)
    )
    for key in keys:
        memory = RESULTS_OFFSET + ((key - 0x0A00) << 8)
        code += Op.SSTORE(key, Op.MLOAD(memory))
    return code


@pytest.mark.ported_from(
    [
        "state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromTransactionFiller.yml",  # noqa: E501
        "state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromCalledContractFiller.yml",  # noqa: E501
        "state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromContractInitializationFiller.yml",  # noqa: E501
        "state_tests/stStaticFlagEnabled/DelegatecallToPrecompileFromTransactionFiller.yml",  # noqa: E501
        "state_tests/stStaticFlagEnabled/DelegatecallToPrecompileFromCalledContractFiller.yml",  # noqa: E501
        "state_tests/stStaticFlagEnabled/DelegatecallToPrecompileFromContractInitializationFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode, entry",
    [
        pytest.param(
            Op.CALLCODE,
            "transaction",
            id="callcode_to_precompile_from_transaction",
        ),
        pytest.param(
            Op.CALLCODE,
            "called_contract",
            id="callcode_to_precompile_from_called_contract",
        ),
        pytest.param(
            Op.CALLCODE,
            "contract_initialization",
            id="callcode_to_precompile_from_contract_initialization",
        ),
        pytest.param(
            Op.DELEGATECALL,
            "transaction",
            id="delegatecall_to_precompile_from_transaction",
        ),
        pytest.param(
            Op.DELEGATECALL,
            "called_contract",
            id="delegatecall_to_precompile_from_called_contract",
        ),
        pytest.param(
            Op.DELEGATECALL,
            "contract_initialization",
            id="delegatecall_to_precompile_from_contract_initialization",
        ),
    ],
)
def test_call_to_precompile_in_static_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    entry: str,
) -> None:
    """
    Call every precompile from a contract reached through STATICCALL.

    The reader is the transaction target, a contract called by the
    target, or the init code of a contract created by the target.
    """
    sender = pre.fund_eoa()
    caller_code, results = precompile_caller(opcode)
    caller = pre.deploy_contract(code=caller_code, balance=1000)
    reader_code = results_reader(caller, sorted(results))
    reader_storage = {0: FEED, 1: FEED, **results}
    post = {caller: Account(storage={}, balance=1000)}

    if entry == "transaction":
        reader = pre.deploy_contract(
            code=reader_code, storage={0: DEADBEAF, 1: DEADBEAF}
        )
        tx = Transaction(sender=sender, to=reader)
        post[reader] = Account(storage=reader_storage)
    elif entry == "called_contract":
        reader = pre.deploy_contract(
            code=reader_code, storage={0: DEADBEAF, 1: DEADBEAF}
        )
        entry_contract = pre.deploy_contract(
            code=Op.SSTORE(0, FEED)
            + Op.POP(Op.CALL(address=reader))
            + Op.SSTORE(1, FEED),
            storage={0: DEADBEAF, 1: DEADBEAF},
        )
        tx = Transaction(sender=sender, to=entry_contract)
        post[reader] = Account(storage=reader_storage)
        post[entry_contract] = Account(storage={0: FEED, 1: FEED})
    elif entry == "contract_initialization":
        salt = 0x5A175A17
        creator = pre.deploy_contract(
            code=Op.SSTORE(0, FEED)
            + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.SSTORE(1, Op.CREATE2(0, 0, Op.CALLDATASIZE, salt))
            + Op.SSTORE(2, FEED),
            storage={0: DEADBEAF, 1: DEADBEAF},
        )
        created = compute_create2_address(creator, salt, reader_code)
        tx = Transaction(sender=sender, to=creator, data=reader_code)
        post[creator] = Account(storage={0: FEED, 1: created, 2: FEED})
        post[created] = Account(storage=reader_storage)
    else:
        raise ValueError(f"unknown entry: {entry}")

    state_test(pre=pre, post=post, tx=tx)
