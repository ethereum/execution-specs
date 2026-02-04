from execution_testing import (
    Account,
    Alloc,
    BenchmarkTestFiller,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Macros as Om,
    Op,
    Transaction,
    While,
)
from execution_testing.cli.pytest_commands.plugins.execute.pre_alloc import (
    AddressStubs,
)
from execution_testing.test_types.phase_manager import TestPhaseManager

# TODO make this available as "stub" also (but default to this address)
XEN_ADDRESS = 0x06450DEE7FD2FB8E39061434BABCFC05599A6FB8

SELECTOR_BALANCEOF = bytes.fromhex("70A08231")

def test_xen_read_balance_nonexisting(benchmark_test: BenchmarkTestFiller,
                                      pre: Alloc, gas_benchmark_value: int) -> None:
    # The threshold should be enough to perform the final SSTORE 
    # (all gas beyond the while loop_)
    # The EVM logic takes care of how much gas the loop actually takes.
    threshold = 30_000

    loop_code = (
        Op.MSTORE(4, Op.ADD(Op.MLOAD(4), Op.CALL(address=XEN_ADDRESS,
                                                 args_offset=0,
                                                 args_size=36)))
    )

    init_loop_code = Om.MSTORE(SELECTOR_BALANCEOF) + Op.MSTORE(4, Op.SLOAD(0))

    code = (init_loop_code + loop_code + 
            Op.MSTORE(36, Op.ADD(Op.GAS + loop_code + Op.GAS + Op.SWAP1 + Op.SUB, threshold))
    + While(body = loop_code, condition=Op.GT(Op.GAS, Op.MLOAD(36))
    + Op.SSTORE(0, Op.MLOAD(4))))

    attack_contract = pre.deploy_contract(code)

    tx = Transaction(
        to=attack_contract,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)