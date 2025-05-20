"""
abstract: Tests [EIP-152: BLAKE2b compression precompile](https://eips.ethereum.org/EIPS/eip-152)
    Test cases for [EIP-152: BLAKE2b compression precompile](https://eips.ethereum.org/EIPS/eip-152).
"""

from typing import Union

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Bytecode,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import Blake2bInput, ExpectedOutput
from .spec import SpecTestVectors, ref_spec_152

REFERENCE_SPEC_GIT_PATH = ref_spec_152.git_path
REFERENCE_SPEC_VERSION = ref_spec_152.version


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/blake2BFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLBlake2fFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEBlake2fFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/delegatecall09UndefinedFiller.yml",
    ],
    pr=[
        "https://github.com/ethereum/execution-spec-tests/pull/1244",
        "https://github.com/ethereum/execution-spec-tests/pull/1067",
    ],
)
@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize("call_opcode", [Op.CALL])
@pytest.mark.parametrize(
    ["data", "output"],
    [
        pytest.param(
            Blake2bInput(
                rounds=0,
                rounds_length=0,
                h="",
                m="",
                t_0="",
                t_1="",
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="empty-input",
        ),
        pytest.param(
            Blake2bInput(
                rounds_length=3,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="invalid-rounds-length-short",
        ),
        pytest.param(
            Blake2bInput(
                rounds_length=5,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="invalid-rounds-length-long",
        ),
        pytest.param(
            Blake2bInput(
                f=2,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="invalid-final-block-flag-value-0x02",
        ),
        pytest.param(
            Blake2bInput(
                rounds=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x08c9bcf367e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5",
                data_2="0xd282e6ad7f520e511f6c3e2b8c68059b9442be0454267ce079217e1319cde05b",
            ),
            id="valid-rounds-0",
        ),
        pytest.param(
            Blake2bInput(),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d1",
                data_2="0x7d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923",
            ),
            id="valid-rounds-12",
        ),
        pytest.param(
            Blake2bInput(
                f=False,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x75ab69d3190a562c51aef8d88f1c2775876944407270c42c9844252c26d28752",
                data_2="0x98743e7f6d5ea2f2d3e8d226039cd31b4e426ac4f2d3d666a610c2116fde4735",
            ),
            id="valid-false-final-block-flag",
        ),
        pytest.param(
            Blake2bInput(
                rounds=1,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xb63a380cb2897d521994a85234ee2c181b5f844d2c624c002677e9703449d2fb",
                data_2="0xa551b3a8333bcdf5f2f7e08993d53923de3d64fcc68c034e717b9293fed7a421",
            ),
            id="valid-rounds-1",
        ),
        # Excessive number of rounds expects to run out of gas
        pytest.param(
            Blake2bInput(
                rounds=4294967295,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x0",
                data_2="0x0",
            ),
            id="oog-rounds-4294967295",
        ),
        # Case from https://github.com/ethereum/tests/pull/948#issuecomment-925964632
        pytest.param(
            Blake2bInput(
                m="6162636465000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=5,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xf3e89a60ec4b0b1854744984e421d22b82f181bd4601fb9b1726b2662da61c29",
                data_2="0xdff09e75814acb2639fd79e56616e55fc135f8476f0302b3dc8d44e082eb83a8",
            ),
            id="valid-different-message-offset-0x05",
        ),
        pytest.param(
            Blake2bInput(
                rounds=16,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xa8ef8236e5f48a74af375df15681d128457891c1cc4706f30747b2d40300b2f4",
                data_2="0x9d19f80fbd0945fd87736e1fc1ff10a80fd85a7aa5125154f3aaa3789ddff673",
            ),
            id="valid-rounds-16",
        ),
        pytest.param(
            Blake2bInput(
                rounds=32,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xbc5e888ed71b546da7b1506179bdd6c184a6410c40de33f9c330207417797889",
                data_2="0x5dbe74144468aefe5c2afce693c62dbca99e5e076dd467fe90a41278b16d691e",
            ),
            id="valid-rounds-32",
        ),
        pytest.param(
            Blake2bInput(
                rounds=64,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x74097ae7b16ffd18c742aee5c55dc89d54b6f1a8a19e6139ccfb38afba56b6b0",
                data_2="0x2cc35c441c19c21194fefb6841e72202f7c9d05eb9c3cfd8f94c67aa77d473c1",
            ),
            id="valid-rounds-64",
        ),
        pytest.param(
            Blake2bInput(
                rounds=128,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xd82c6a670dc90af9d7f77644eacbeddfed91b760c65c927871784abceaab3f81",
                data_2="0x3759733a1736254fb1cfc515dbfee467930955af56e27ee435f836fc3e65969f",
            ),
            id="valid-rounds-128",
        ),
        pytest.param(
            Blake2bInput(
                rounds=256,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x5d6ff04d5ebaee5687d634613ab21e9a7d36f782033c74f91d562669aaf9d592",
                data_2="0xc86346cb2df390243a952834306b389e656876a67934e2c023bce4918a016d4e",
            ),
            id="valid-rounds-256",
        ),
        pytest.param(
            Blake2bInput(
                rounds=512,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xa2c1eb780a6e1249156fe0751e5d4687ea9357b0651c78df660ab004cb477363",
                data_2="0x6298bbbc683e4a0261574b6d857a6a99e06b2eea50b16f86343d2625ff222b98",
            ),
            id="valid-rounds-512",
        ),
        pytest.param(
            Blake2bInput(
                rounds=1024,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x689419d2bf32b5a9901a2c733b9946727026a60d8773117eabb35f04a52cdcf1",
                data_2="0xb8fb4473454cf03d46c36a10b3f784aae4dc80a24424960e66a8ad5a8c2bfb30",
            ),
            id="valid-rounds-1024",
        ),
        pytest.param(
            Blake2bInput(
                rounds=16,
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x4ab6df9d1f57140bbd27b5e164f42102d9e2b0bf4d53da501273f81a37e505c7",
                data_2="0xf6e136f9ca4b693aa6e990b04c6412296dc09540c23c395f183011a0c5d7392e",
            ),
            id="valid-rounds-16-offset-0x10",
        ),
        pytest.param(
            Blake2bInput(
                rounds=32,
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x7af9b4f9c25ba3e3fd4fcb957e703b7b2e648990fe8e24c6ca2a2dfac4ce76e6",
                data_2="0x18acffc26913d6759843362adeb4c95299777baaa977b5d94dd219d1777e4cb",
            ),
            id="valid-rounds-32-offset-0x10",
        ),
        pytest.param(
            Blake2bInput(
                rounds=64,
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x97eb79f7abc085a3da64d6e8643d196cbf522a51985ba2cc6a7ca14289b59df0",
                data_2="0x73366eb68e41966eb8b33ab5bd6078d0de2fa4edc986b1d2afc4c92f2fc30cda",
            ),
            id="valid-rounds-64-offset-0x10",
        ),
        pytest.param(
            Blake2bInput(
                rounds=128,
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x5ef3d6ee148936390a9053e91ab5a92f4de4dfc62ebb95d71485be26d9b78c8d",
                data_2="0x8989dfe319f2fb5f11784174db63a7bcfc50de04e13fad57bea159e46e8811df",
            ),
            id="valid-rounds-128-offset-0x10",
        ),
        pytest.param(
            Blake2bInput(
                rounds=256,
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xa36be13275fec9a91779f0c9b06b1b40d8c8a13ab0786d0764c2eb708cc8eb81",
                data_2="0xf1acb2a3c7abd2ff5a9fdfe88b81f6f56288dc5260a9c810f023ae83b9b64a1a",
            ),
            id="valid-rounds-256-offset-0x10",
        ),
        pytest.param(
            Blake2bInput(
                rounds=512,
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xc987e560e3f90833c0d10ae1282bd9d35a7ba06d8abaa13a994d0962ed2bbaa9",
                data_2="0xf69c1e1e7c9aedb75e72d1b46e9f1b2ad8f8c2f7f858a04ed8aec16f964a96da",
            ),
            id="valid-rounds-512-offset-0x10",
        ),
        pytest.param(
            Blake2bInput(
                rounds=1024,
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x224138a6afa847230ff09c23e2ca66522e22d26884b09d7740e2dd127cb61057",
                data_2="0x90cecbd4de6a52a733ca4a59583c064ad6ec7653d5d457b681de332f16f3d45",
            ),
            id="valid-rounds-1024-offset-0x10",
        ),
        pytest.param(
            Blake2bInput(
                rounds=16,
                m="6162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d900000000000000",
                t_0=120,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xabcd200f2962ede252fc455ea70d12b236ad2f4046b91e17558a7741d9da39a2",
                data_2="0x548083b610bb8591ca50418eabd15b6489a936b178a435b4c182ffa475eba4d8",
            ),
            id="valid-rounds-16-offset-0x78",
        ),
        pytest.param(
            Blake2bInput(
                rounds=32,
                m="6162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d900000000000000",
                t_0=120,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x39fc2077154fba422b3d628d10908c596beebea8dfd90f14566aec4f60bdb2bc",
                data_2="0xa75d73ab2b224d58c3568cbc7fc8905cc849f10745f00addef02384032d53729",
            ),
            id="valid-rounds-32-offset-0x78",
        ),
        pytest.param(
            Blake2bInput(
                rounds=64,
                m="6162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d900000000000000",
                t_0=120,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x5bb981381beb687d5fdbe5e7c096fbd1ce193b780948c1d74ebbb7c58db364c7",
                data_2="0xb7695d32f918444dbdcbdcff476fc70a926e228c4cbb7d05473711d3b56e5b33",
            ),
            id="valid-rounds-64-offset-0x78",
        ),
        pytest.param(
            Blake2bInput(
                rounds=0,
                rounds_length=0,
                h="00",
                m="00",
                t_0=0,
                t_1=SpecTestVectors.BLAKE2_OFFSET_COUNTER_1,
                f=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-RFC-7693-zero-input",
        ),
    ],
)
def test_blake2b(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    blake2b_contract_bytecode: Bytecode,
    data: Union[Blake2bInput, str, bytes],
    output: ExpectedOutput,
):
    """Test BLAKE2b precompile."""
    env = Environment()

    account = pre.deploy_contract(blake2b_contract_bytecode, storage={0: 0xDEADBEEF})
    sender = pre.fund_eoa()

    if isinstance(data, Blake2bInput):
        data = data.create_blake2b_tx_data()
    elif isinstance(data, str):
        data = bytes.fromhex(data)

    if isinstance(data, Blake2bInput):
        data = data.create_blake2b_tx_data()
    elif isinstance(data, str):
        data = bytes.fromhex(data)

    tx = Transaction(
        ty=0x0,
        to=account,
        data=data,
        gas_limit=1_000_000,
        protected=True,
        sender=sender,
        value=100000,
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


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/blake2BFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLBlake2fFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEBlake2fFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/delegatecall09UndefinedFiller.yml",
    ],
    pr=[
        "https://github.com/ethereum/execution-spec-tests/pull/1244",
        "https://github.com/ethereum/execution-spec-tests/pull/1067",
    ],
)
@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize("call_opcode", [Op.CALL, Op.CALLCODE])
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
                rounds_length=3,
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
                rounds_length=5,
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
    call_opcode: Op,
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


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/blake2BFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLBlake2fFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEBlake2fFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/delegatecall09UndefinedFiller.yml",
    ],
    pr=[
        "https://github.com/ethereum/execution-spec-tests/pull/1244",
        "https://github.com/ethereum/execution-spec-tests/pull/1067",
    ],
)
@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize("call_opcode", [Op.CALL, Op.CALLCODE])
@pytest.mark.parametrize("gas_limit", [Environment().gas_limit, 90_000, 110_000, 200_000])
@pytest.mark.parametrize(
    ["data", "output"],
    [
        pytest.param(
            Blake2bInput(
                rounds=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x08c9bcf367e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5",
                data_2="0xd282e6ad7f520e511f6c3e2b8c68059b9442be0454267ce079217e1319cde05b",
            ),
            id="EIP-152-case3-data4-gas-limit",
        ),
        pytest.param(
            Blake2bInput(),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d1",
                data_2="0x7d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923",
            ),
            id="EIP-152-case4-data5-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
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
                t_1=SpecTestVectors.BLAKE2_OFFSET_COUNTER_1,
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
    call_opcode: Op,
    blake2b_contract_bytecode: Bytecode,
    gas_limit: int,
    data: Union[Blake2bInput, str, bytes],
    output: ExpectedOutput,
):
    """Test BLAKE2b precompile with different gas limits."""
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
    state_test(
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/blake2BFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLBlake2fFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEBlake2fFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/delegatecall09UndefinedFiller.yml",
    ],
    pr=[
        "https://github.com/ethereum/execution-spec-tests/pull/1244",
        "https://github.com/ethereum/execution-spec-tests/pull/1067",
    ],
)
@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize("call_opcode", [Op.CALL, Op.CALLCODE])
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
                rounds_length=3,
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
                rounds_length=5,
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
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x165da71a32e91bca2623bfaeab079f7e6edfba2259028cc854ec497f9fb0fe75",
                data_2="0xd37f63034b83f4a0a07cd238483874862921ef0c40630826a76e41bf3b02ffe3",
            ),
            id="EIP-152-modified-case8-data9-large-gas-limit",
        ),
        pytest.param(
            Blake2bInput(
                rounds=8000000,
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
@pytest.mark.slow()
def test_blake2b_large_gas_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
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
        gas_limit=env.gas_limit,
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
