"""
abstract: Tests [EIP-152: BLAKE2b compression precompile](https://eips.ethereum.org/EIPS/eip-152)
    Test cases for [EIP-152: BLAKE2b compression precompile](https://eips.ethereum.org/EIPS/eip-152).
"""

from dataclasses import dataclass
from typing import Union

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Bytecode,
    Environment,
    StateTestFiller,
    TestParameterGroup,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-152.md"
REFERENCE_SPEC_VERSION = "2762bfcff3e549ef263342e5239ef03ac2b07400"


@dataclass(kw_only=True, frozen=True, repr=False)
class Blake2bInput(TestParameterGroup):
    """
    Helper class that defines the BLAKE2b precompile inputs and creates the
    call data from them. Returns all inputs encoded as bytes.

    Attributes:
        rounds_length (int): An optional integer representing the bytes length
            for the number of rounds. Defaults to the expected length of 4.
        rounds (int | str): A hex string or integer value representing the number of rounds.
        h (str): A hex string that represents the state vector.
        m (str): A hex string that represents the message block vector.
        t_0 (int | str): A hex string or integer value that represents the first offset counter.
        t_1 (int | str): A hex string or integer value that represents the second offset counter.
        f (bool): An optional boolean that represents the final block indicator flag.
            Defaults to True.

    """

    rounds_length: int = 4
    rounds: int | str
    h: str
    m: str
    t_0: int | str
    t_1: int | str
    f: bool | int = True

    def create_blake2b_tx_data(self):
        """Generate input for the BLAKE2b precompile."""
        _rounds = self.rounds.to_bytes(length=self.rounds_length, byteorder="big")
        _h = bytes.fromhex(self.h)
        _m = bytes.fromhex(self.m)
        _t_0 = (
            bytes.fromhex(self.t_0)
            if isinstance(self.t_0, str)
            else self.t_0.to_bytes(length=8, byteorder="little")
        )
        _t_1 = (
            bytes.fromhex(self.t_1)
            if isinstance(self.t_1, str)
            else self.t_1.to_bytes(length=8, byteorder="little")
        )
        _f = int(self.f).to_bytes(length=1, byteorder="big")

        return _rounds + _h + _m + _t_0 + _t_1 + _f


@dataclass(kw_only=True, frozen=True, repr=False)
class ExpectedOutput(TestParameterGroup):
    """
    Expected test result.

    Attributes:
        call_succeeds (str | bool): A hex string or boolean to indicate whether the call was
            successful or not.
        data_1 (str): String value of the first updated state vector.
        data_2 (str): String value of the second updated state vector.

    """

    call_succeeds: str | bool
    data_1: str
    data_2: str


@pytest.fixture
def blake2b_contract_bytecode():
    """Contract code that performs a CALL to the BLAKE2b precompile and stores the result."""
    return (
        # Store all CALLDATA into memory (offset 0)
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        # Store the returned CALL status (success = 1, fail = 0) into slot 0:
        + Op.SSTORE(
            0,
            # Setup stack to CALL into Blake2b with the CALLDATA and CALL into it (+ pop value)
            Op.CALLCODE(
                address=9,
                args_offset=0,
                args_size=Op.CALLDATASIZE(),
                ret_offset=0x200,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(1, Op.MLOAD(0x200))
        + Op.SSTORE(2, Op.MLOAD(0x220))
        + Op.STOP()
    )


@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize("gas_limit", [90_000, 110_000, 200_000])
@pytest.mark.parametrize(
    ["data", "output"],
    [
        pytest.param(
            b"",
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case1-data0-invalid-low-gas",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                rounds_length=3,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case1-data1-invalid-low-gas",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                rounds_length=5,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case1-data2-invalid-low-gas",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
                f=2,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case1-data3-invalid-low-gas",
        ),
        pytest.param(
            Blake2bInput(
                rounds=8000000,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case1-data9-invalid-low-gas",
        ),
        pytest.param(
            "000c",
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case1-data10-invalid-low-gas",
        ),
    ],
)
def test_blake2b_invalid_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    blake2b_contract_bytecode: Bytecode,
    gas_limit: int,
    data: Union[Blake2bInput, str, bytes],
    output: ExpectedOutput,
):
    """Test BLAKE2b precompile invalid calls using different gas limits."""
    env = Environment()

    account = pre.deploy_contract(blake2b_contract_bytecode, storage={0: 0xDEADBEEF})
    sender = pre.fund_eoa()

    if isinstance(data, Blake2bInput):
        data = data.create_blake2b_tx_data()
    elif isinstance(data, str):
        data = bytes.fromhex(data)

    tx = Transaction(
        ty=0x0,
        to=account,
        data=data,
        gas_limit=gas_limit,
        protected=True,
        sender=sender,
        value=0,
    )

    post = {
        account: Account(
            storage={
                0: 0xDEADBEEF,
                1: output.data_1,
                2: output.data_2,
            },
            nonce=0x1,
        )
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize("gas_limit", [100_000_000, 90_000, 110_000, 200_000])
@pytest.mark.parametrize(
    ["data", "output"],
    [
        pytest.param(
            Blake2bInput(
                rounds=0,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x08c9bcf367e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5",
                data_2="0xd282e6ad7f520e511f6c3e2b8c68059b9442be0454267ce079217e1319cde05b",
            ),
            id="EIP-152-case3-data4-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d1",
                data_2="0x7d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923",
            ),
            id="EIP-152-case4-data5-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
                f=False,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x75ab69d3190a562c51aef8d88f1c2775876944407270c42c9844252c26d28752",
                data_2="0x98743e7f6d5ea2f2d3e8d226039cd31b4e426ac4f2d3d666a610c2116fde4735",
            ),
            id="EIP-152-case5-data6-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
                rounds=1,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xb63a380cb2897d521994a85234ee2c181b5f844d2c624c002677e9703449d2fb",
                data_2="0xa551b3a8333bcdf5f2f7e08993d53923de3d64fcc68c034e717b9293fed7a421",
            ),
            id="EIP-152-case6-data7-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
                rounds=0,
                h="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                m="0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=0,
                t_1=0,
                f=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x08c9bcf367e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5",
                data_2="0xd182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
            ),
            id="EIP-152-case7-data8-gas-limit",
        ),
    ],
)
def test_blake2b_gas_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    blake2b_contract_bytecode: Bytecode,
    gas_limit: int,
    data: Union[Blake2bInput, str, bytes],
    output: ExpectedOutput,
):
    """Test BLAKE2b precompile with different gas limits."""
    env = Environment()

    account = pre.deploy_contract(blake2b_contract_bytecode, storage={0: 0xDEADBEEF})
    sender = pre.fund_eoa()

    if isinstance(data, Blake2bInput):
        data = data.create_blake2b_tx_data()
    elif isinstance(data, str):
        data = bytes.fromhex(data)

    tx = Transaction(
        ty=0x0,
        to=account,
        data=data,
        gas_limit=gas_limit,
        protected=True,
        sender=sender,
        value=0,
    )

    post = {
        account: Account(
            storage={
                0: 0x1 if output.call_succeeds else 0x0,
                1: output.data_1,
                2: output.data_2,
            }
        )
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize(
    ["data", "output"],
    [
        pytest.param(
            b"",
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case0-data0-large-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                rounds_length=3,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case2-data1-large-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                rounds_length=5,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case2-data2-large-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
                f=2,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case2-data3-large-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
                rounds=100_000,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",  # noqa: E501
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x165da71a32e91bca2623bfaeab079f7e6edfba2259028cc854ec497f9fb0fe75",
                data_2="0xd37f63034b83f4a0a07cd238483874862921ef0c40630826a76e41bf3b02ffe3",
            ),
            id="EIP-152-modified-case8-data9-large-gas-limit",
            marks=pytest.mark.slow,
        ),
        pytest.param(
            Blake2bInput(
                rounds=8000000,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",  # noqa: E501
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x6d2ce9e534d50e18ff866ae92d70cceba79bbcd14c63819fe48752c8aca87a4b",
                data_2="0xb7dcc230d22a4047f0486cfcfb50a17b24b2899eb8fca370f22240adb5170189",
            ),
            id="EIP-152-case8-data9-large-gas-limit",
            marks=pytest.mark.skip("Times-out during fill"),
        ),
        pytest.param(
            "000c",
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case9-data10-large-gas-limit",
        ),
    ],
)
def test_blake2b_large_gas_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    blake2b_contract_bytecode: Bytecode,
    data: Union[Blake2bInput, str, bytes],
    output: ExpectedOutput,
):
    """Test BLAKE2b precompile with large gas limit."""
    env = Environment()

    account = pre.deploy_contract(blake2b_contract_bytecode, storage={0: 0xDEADBEEF})
    sender = pre.fund_eoa()

    if isinstance(data, Blake2bInput):
        data = data.create_blake2b_tx_data()
    elif isinstance(data, str):
        data = bytes.fromhex(data)

    tx = Transaction(
        ty=0x0,
        to=account,
        data=data,
        gas_limit=100_000_000,
        protected=True,
        sender=sender,
        value=0,
    )

    post = {
        account: Account(
            storage={
                0: 0x1 if output.call_succeeds else 0x0,
                1: output.data_1,
                2: output.data_2,
            }
        )
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
