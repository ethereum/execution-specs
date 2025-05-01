"""Pre-allocation fixtures using for test filling."""

from itertools import count
from random import randint
from typing import Generator, Iterator, List, Literal, Tuple

import pytest
from pydantic import PrivateAttr

from ethereum_test_base_types import Bytes, Number, StorageRootType, ZeroPaddedHexNumber
from ethereum_test_base_types.conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
)
from ethereum_test_forks import Fork
from ethereum_test_rpc import EthRPC
from ethereum_test_rpc.types import TransactionByHashResponse
from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    AuthorizationTuple,
    Initcode,
    Storage,
    Transaction,
)
from ethereum_test_tools import Alloc as BaseAlloc
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types.eof.v1 import Container
from ethereum_test_vm import Bytecode, EVMCodeType, Opcodes

MAX_BYTECODE_SIZE = 24576

MAX_INITCODE_SIZE = MAX_BYTECODE_SIZE * 2


def pytest_addoption(parser):
    """Add command-line options to pytest."""
    pre_alloc_group = parser.getgroup(
        "pre_alloc", "Arguments defining pre-allocation behavior during test execution"
    )
    pre_alloc_group.addoption(
        "--eoa-start",
        action="store",
        dest="eoa_iterator_start",
        default=randint(0, 2**256),
        type=int,
        help="The start private key from which tests will deploy EOAs.",
    )
    pre_alloc_group.addoption(
        "--evm-code-type",
        action="store",
        dest="evm_code_type",
        default=None,
        type=EVMCodeType,
        choices=list(EVMCodeType),
        help="Type of EVM code to deploy in each test by default.",
    )
    pre_alloc_group.addoption(
        "--eoa-fund-amount-default",
        action="store",
        dest="eoa_fund_amount_default",
        default=10**18,
        type=int,
        help="The default amount of wei to fund each EOA in each test with.",
    )


@pytest.hookimpl(trylast=True)
def pytest_report_header(config):
    """Pytest hook called to obtain the report header."""
    bold = "\033[1m"
    reset = "\033[39;49m"
    eoa_start = config.getoption("eoa_iterator_start")
    header = [
        (bold + f"Start seed for EOA: {hex(eoa_start)} " + reset),
    ]
    return header


@pytest.fixture(scope="session")
def eoa_iterator(request) -> Iterator[EOA]:
    """Return an iterator that generates EOAs."""
    eoa_start = request.config.getoption("eoa_iterator_start")
    print(f"Starting EOA index: {hex(eoa_start)}")
    return iter(EOA(key=i, nonce=0) for i in count(start=eoa_start))


class Alloc(BaseAlloc):
    """A custom class that inherits from the original Alloc class."""

    _fork: Fork = PrivateAttr()
    _sender: EOA = PrivateAttr()
    _eth_rpc: EthRPC = PrivateAttr()
    _txs: List[Transaction] = PrivateAttr(default_factory=list)
    _deployed_contracts: List[Tuple[Address, Bytes]] = PrivateAttr(default_factory=list)
    _funded_eoa: List[EOA] = PrivateAttr(default_factory=list)
    _evm_code_type: EVMCodeType | None = PrivateAttr(None)
    _chain_id: int = PrivateAttr()

    def __init__(
        self,
        *args,
        fork: Fork,
        sender: EOA,
        eth_rpc: EthRPC,
        eoa_iterator: Iterator[EOA],
        chain_id: int,
        eoa_fund_amount_default: int,
        evm_code_type: EVMCodeType | None = None,
        **kwargs,
    ):
        """Initialize the pre-alloc with the given parameters."""
        super().__init__(*args, **kwargs)
        self._fork = fork
        self._sender = sender
        self._eth_rpc = eth_rpc
        self._eoa_iterator = eoa_iterator
        self._evm_code_type = evm_code_type
        self._chain_id = chain_id
        self._eoa_fund_amount_default = eoa_fund_amount_default

    def __setitem__(self, address: Address | FixedSizeBytesConvertible, account: Account | None):
        """Set account associated with an address."""
        raise ValueError("Tests are not allowed to set pre-alloc items in execute mode")

    def code_pre_processor(
        self, code: Bytecode | Container, *, evm_code_type: EVMCodeType | None
    ) -> Bytecode | Container:
        """Pre-processes the code before setting it."""
        if evm_code_type is None:
            evm_code_type = self._evm_code_type
        if evm_code_type == EVMCodeType.EOF_V1:
            if not isinstance(code, Container):
                if isinstance(code, Bytecode) and not code.terminating:
                    return Container.Code(code + Opcodes.STOP)
                return Container.Code(code)
        return code

    def deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType | None = None,
        balance: NumberConvertible = 0,
        nonce: NumberConvertible = 1,
        address: Address | None = None,
        evm_code_type: EVMCodeType | None = None,
        label: str | None = None,
    ) -> Address:
        """Deploy a contract to the allocation."""
        if storage is None:
            storage = {}
        assert address is None, "address parameter is not supported"

        if not isinstance(storage, Storage):
            storage = Storage(storage)  # type: ignore

        initcode_prefix = Bytecode()

        deploy_gas_limit = 21_000 + 32_000

        if len(storage.root) > 0:
            initcode_prefix += sum(Op.SSTORE(key, value) for key, value in storage.root.items())
            deploy_gas_limit += len(storage.root) * 22_600

        assert isinstance(code, Bytecode) or isinstance(code, Container), (
            f"incompatible code type: {type(code)}"
        )
        code = self.code_pre_processor(code, evm_code_type=evm_code_type)

        assert len(code) <= MAX_BYTECODE_SIZE, f"code too large: {len(code)} > {MAX_BYTECODE_SIZE}"

        deploy_gas_limit += len(bytes(code)) * 200

        initcode: Bytecode | Container

        if evm_code_type == EVMCodeType.EOF_V1:
            assert isinstance(code, Container)
            initcode = Container.Init(deploy_container=code, initcode_prefix=initcode_prefix)
        else:
            initcode = Initcode(deploy_code=code, initcode_prefix=initcode_prefix)
            memory_expansion_gas_calculator = self._fork.memory_expansion_gas_calculator()
            deploy_gas_limit += memory_expansion_gas_calculator(new_bytes=len(bytes(initcode)))

        assert len(initcode) <= MAX_INITCODE_SIZE, (
            f"initcode too large {len(initcode)} > {MAX_INITCODE_SIZE}"
        )

        calldata_gas_calculator = self._fork.calldata_gas_calculator()
        deploy_gas_limit += calldata_gas_calculator(data=initcode)

        # Limit the gas limit
        deploy_gas_limit = min(deploy_gas_limit * 2, 30_000_000)
        print(f"Deploying contract with gas limit: {deploy_gas_limit}")

        deploy_tx = Transaction(
            sender=self._sender,
            to=None,
            data=initcode,
            value=balance,
            gas_limit=deploy_gas_limit,
        ).with_signature_and_sender()
        self._eth_rpc.send_transaction(deploy_tx)
        self._txs.append(deploy_tx)

        contract_address = deploy_tx.created_contract
        self._deployed_contracts.append((contract_address, Bytes(code)))

        assert Number(nonce) >= 1, "impossible to deploy contract with nonce lower than one"

        super().__setitem__(
            contract_address,
            Account(
                nonce=nonce,
                balance=balance,
                code=code,
                storage=storage,
            ),
        )

        contract_address.label = label
        return contract_address

    def fund_eoa(
        self,
        amount: NumberConvertible | None = None,
        label: str | None = None,
        storage: Storage | None = None,
        delegation: Address | Literal["Self"] | None = None,
        nonce: NumberConvertible | None = None,
    ) -> EOA:
        """Add a previously unused EOA to the pre-alloc with the balance specified by `amount`."""
        assert nonce is None, "nonce parameter is not supported for execute"
        eoa = next(self._eoa_iterator)
        # Send a transaction to fund the EOA
        if amount is None:
            amount = self._eoa_fund_amount_default

        fund_tx: Transaction | None = None
        if delegation is not None or storage is not None:
            if storage is not None:
                sstore_address = self.deploy_contract(
                    code=(
                        sum(Op.SSTORE(key, value) for key, value in storage.root.items()) + Op.STOP
                    )
                )
                set_storage_tx = Transaction(
                    sender=self._sender,
                    to=eoa,
                    authorization_list=[
                        AuthorizationTuple(
                            chain_id=self._chain_id,
                            address=sstore_address,
                            nonce=eoa.nonce,
                            signer=eoa,
                        ),
                    ],
                    gas_limit=100_000,
                ).with_signature_and_sender()
                eoa.nonce = Number(eoa.nonce + 1)
                self._eth_rpc.send_transaction(set_storage_tx)
                self._txs.append(set_storage_tx)

            if delegation is not None:
                if not isinstance(delegation, Address) and delegation == "Self":
                    delegation = eoa
                # TODO: This tx has side-effects on the EOA state because of the delegation
                fund_tx = Transaction(
                    sender=self._sender,
                    to=eoa,
                    value=amount,
                    authorization_list=[
                        AuthorizationTuple(
                            chain_id=self._chain_id,
                            address=delegation,
                            nonce=eoa.nonce,
                            signer=eoa,
                        ),
                    ],
                    gas_limit=100_000,
                ).with_signature_and_sender()
                eoa.nonce = Number(eoa.nonce + 1)
            else:
                fund_tx = Transaction(
                    sender=self._sender,
                    to=eoa,
                    value=amount,
                    authorization_list=[
                        AuthorizationTuple(
                            chain_id=self._chain_id,
                            address=0,  # Reset delegation to an address without code
                            nonce=eoa.nonce,
                            signer=eoa,
                        ),
                    ],
                    gas_limit=100_000,
                ).with_signature_and_sender()
                eoa.nonce = Number(eoa.nonce + 1)

        else:
            if Number(amount) > 0:
                fund_tx = Transaction(
                    sender=self._sender,
                    to=eoa,
                    value=amount,
                ).with_signature_and_sender()

        if fund_tx is not None:
            self._eth_rpc.send_transaction(fund_tx)
            self._txs.append(fund_tx)
        super().__setitem__(
            eoa,
            Account(
                nonce=eoa.nonce,
                balance=amount,
            ),
        )
        self._funded_eoa.append(eoa)
        return eoa

    def fund_address(self, address: Address, amount: NumberConvertible):
        """
        Fund an address with a given amount.

        If the address is already present in the pre-alloc the amount will be
        added to its existing balance.
        """
        fund_tx = Transaction(
            sender=self._sender,
            to=address,
            value=amount,
        ).with_signature_and_sender()
        self._eth_rpc.send_transaction(fund_tx)
        self._txs.append(fund_tx)
        if address in self:
            account = self[address]
            if account is not None:
                current_balance = account.balance or 0
                account.balance = ZeroPaddedHexNumber(current_balance + Number(amount))
                return

        super().__setitem__(address, Account(balance=amount))

    def empty_account(self) -> Address:
        """
        Add a previously unused account guaranteed to be empty to the pre-alloc.

        This ensures the account has:
        - Zero balance
        - Zero nonce
        - No code
        - No storage

        This is different from precompiles or system contracts. The function does not
        send any transactions, ensuring that the account remains "empty."

        Returns:
            Address: The address of the created empty account.

        """
        eoa = next(self._eoa_iterator)

        super().__setitem__(
            eoa,
            Account(
                nonce=0,
                balance=0,
            ),
        )
        return Address(eoa)

    def wait_for_transactions(self) -> List[TransactionByHashResponse]:
        """Wait for all transactions to be included in blocks."""
        return self._eth_rpc.wait_for_transactions(self._txs)


@pytest.fixture(autouse=True)
def evm_code_type(request: pytest.FixtureRequest) -> EVMCodeType:
    """Return default EVM code type for all tests (LEGACY)."""
    parameter_evm_code_type = request.config.getoption("evm_code_type")
    if parameter_evm_code_type is not None:
        assert type(parameter_evm_code_type) is EVMCodeType, "Invalid EVM code type"
        return parameter_evm_code_type
    return EVMCodeType.LEGACY


@pytest.fixture(scope="session")
def eoa_fund_amount_default(request: pytest.FixtureRequest) -> int:
    """Get the gas price for the funding transactions."""
    return request.config.option.eoa_fund_amount_default


@pytest.fixture(autouse=True, scope="function")
def pre(
    fork: Fork,
    sender_key: EOA,
    eoa_iterator: Iterator[EOA],
    eth_rpc: EthRPC,
    evm_code_type: EVMCodeType,
    chain_id: int,
    eoa_fund_amount_default: int,
    default_gas_price: int,
) -> Generator[Alloc, None, None]:
    """Return default pre allocation for all tests (Empty alloc)."""
    # Record the starting balance of the sender
    sender_test_starting_balance = eth_rpc.get_balance(sender_key)

    # Prepare the pre-alloc
    pre = Alloc(
        fork=fork,
        sender=sender_key,
        eth_rpc=eth_rpc,
        eoa_iterator=eoa_iterator,
        evm_code_type=evm_code_type,
        chain_id=chain_id,
        eoa_fund_amount_default=eoa_fund_amount_default,
    )

    # Yield the pre-alloc for usage during the test
    yield pre

    # Refund all EOAs (regardless of whether the test passed or failed)
    refund_txs = []
    for eoa in pre._funded_eoa:
        remaining_balance = eth_rpc.get_balance(eoa)
        eoa.nonce = Number(eth_rpc.get_transaction_count(eoa))
        refund_gas_limit = 21_000
        tx_cost = refund_gas_limit * default_gas_price
        if remaining_balance < tx_cost:
            continue
        refund_txs.append(
            Transaction(
                sender=eoa,
                to=sender_key,
                gas_limit=21_000,
                gas_price=default_gas_price,
                value=remaining_balance - tx_cost,
            ).with_signature_and_sender()
        )
    eth_rpc.send_wait_transactions(refund_txs)

    # Record the ending balance of the sender
    sender_test_ending_balance = eth_rpc.get_balance(sender_key)
    used_balance = sender_test_starting_balance - sender_test_ending_balance
    print(f"Used balance={used_balance / 10**18:.18f}")
