"""
EIP Testing Checklist Enum definitions.

Note: This module includes a companion .pyi stub file that provides mypy type hints
for making EIPChecklist classes callable. The stub file is auto-generated using:
    uv run generate_checklist_stubs

If you modify the EIPChecklist class structure, regenerate the stub file to maintain
proper type checking support.
"""

import re

import pytest


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    # Insert an underscore before any uppercase letter that follows a lowercase letter
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert an underscore before any uppercase letter that follows a lowercase letter or number
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class ChecklistItemMeta(type):
    """Metaclass for checklist items that provides string representation."""

    _path: str = ""
    _override_name: str = ""

    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
        """Create a new class with the parent path set."""
        parent_path = kwargs.get("parent_path", "")
        override_name = kwargs.get("override_name", None)

        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)

        cls._override_name = override_name

        # Set the path for this class
        item_name = override_name if override_name is not None else camel_to_snake(name)

        if parent_path:
            # Convert class name to snake_case and append to parent path
            cls._path = f"{parent_path}/{item_name}"
        else:
            cls._path = item_name

        # Process nested classes
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, type) and not attr_name.startswith("_"):
                # Create a new class with the parent path set
                assert isinstance(attr_value, ChecklistItemMeta)
                nested_cls = ChecklistItemMeta(
                    attr_value.__name__,
                    attr_value.__bases__,
                    dict(attr_value.__dict__),
                    parent_path=cls._path,
                    override_name=attr_value._override_name,
                )
                setattr(cls, attr_name, nested_cls)

        return cls

    def __str__(cls) -> str:
        """Return the path for this checklist item."""
        return cls._path

    def __repr__(cls) -> str:
        """Return a representation of this checklist item."""
        return f"<ChecklistItem: {cls._path}>"

    def __call__(cls, *args, **kwargs):
        """Return a pytest mark decorator for the checklist item."""
        # If called with a function as the first argument (direct decorator usage)
        # and no other arguments, apply the decorator to the function
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            func = args[0]
            marker = pytest.mark.eip_checklist(cls._path)
            return marker(func)
        # Otherwise, return a pytest mark decorator
        return pytest.mark.eip_checklist(cls._path, *args, **kwargs)


class ChecklistItem(metaclass=ChecklistItemMeta):
    """Base class for checklist items."""

    pass


class EIPChecklist:
    """
    Main namespace for EIP testing checklist items.

    This class provides a structured way to reference checklist items for EIP testing.
    The class structure is automatically converted to callable pytest markers.

    Note: If you modify this class structure, regenerate the type stub file using:
        uv run generate_checklist_stubs

    Examples:
        @EIPChecklist.Opcode.Test.GasUsage.Normal()
        def test_normal_gas():
            pass

        @EIPChecklist.Opcode.Test.StackOverflow
        def test_stack_overflow():
            pass

    """

    class General(ChecklistItem):
        """General checklist items."""

        class CodeCoverage(ChecklistItem):
            """Code coverage checklist items."""

            class Eels(ChecklistItem):
                """EELS code coverage."""

                pass

            class TestCoverage(ChecklistItem):
                """Test code coverage."""

                pass

            class SecondClient(ChecklistItem):
                """Second client code coverage."""

                pass

    class Opcode(ChecklistItem):
        """New opcode checklist items."""

        class Test(ChecklistItem):
            """Test vectors for new opcode."""

            class MemExp(ChecklistItem):
                """Memory expansion tests."""

                class ZeroBytesZeroOffset(ChecklistItem):
                    """Zero bytes expansion with zero-offset."""

                    pass

                class ZeroBytesMaxOffset(ChecklistItem):
                    """Zero bytes expansion with 2**256-1 offset."""

                    pass

                class SingleByte(ChecklistItem):
                    """Single byte expansion."""

                    pass

                class ThirtyOneBytes(ChecklistItem, override_name="31_bytes"):
                    """31 bytes expansion."""

                    pass

                class ThirtyTwoBytes(ChecklistItem, override_name="32_bytes"):
                    """32 bytes expansion."""

                    pass

                class ThirtyThreeBytes(ChecklistItem, override_name="33_bytes"):
                    """33 bytes expansion."""

                    pass

                class SixtyFourBytes(ChecklistItem, override_name="64_bytes"):
                    """64 bytes expansion."""

                    pass

                class TwoThirtyTwoMinusOneBytes(
                    ChecklistItem, override_name="2_32_minus_one_bytes"
                ):
                    """2**32-1 bytes expansion."""

                    pass

                class TwoThirtyTwoBytes(ChecklistItem, override_name="2_32_bytes"):
                    """2**32 bytes expansion."""

                    pass

                class TwoSixtyFourMinusOneBytes(
                    ChecklistItem, override_name="2_64_minus_one_bytes"
                ):
                    """2**64-1 bytes expansion."""

                    pass

                class TwoSixtyFourBytes(ChecklistItem, override_name="2_64_bytes"):
                    """2**64 bytes expansion."""

                    pass

                class TwoTwoFiftySixMinusOneBytes(
                    ChecklistItem, override_name="2_256_minus_one_bytes"
                ):
                    """2**256-1 bytes expansion."""

                    pass

            class StackOverflow(ChecklistItem):
                """Stack overflow test."""

                pass

            class StackUnderflow(ChecklistItem):
                """Stack underflow test."""

                pass

            class StackComplexOperations(ChecklistItem):
                """Stack complex operations tests."""

                class StackHeights(ChecklistItem):
                    """Stack height tests."""

                    class Zero(ChecklistItem):
                        """Operation on an empty stack."""

                        pass

                    class Odd(ChecklistItem):
                        """Operation on a stack with odd height."""

                        pass

                    class Even(ChecklistItem):
                        """Operation on a stack with even height."""

                        pass

                class DataPortionVariables(ChecklistItem, override_name="data_portion_variables"):
                    """
                    If the opcode contains variables in its data portion, for each variable `n`
                    of the opcode that accesses the nth stack item, test `n` being.
                    """

                    class Top(ChecklistItem):
                        """`n` is the top stack item."""

                        pass

                    class Bottom(ChecklistItem):
                        """`n` is the bottom stack item."""

                        pass

                    class Middle(ChecklistItem):
                        """`n` is the middle stack item."""

                        pass

            class ExecutionContext(ChecklistItem):
                """Execution context tests."""

                class Call(ChecklistItem):
                    """CALL context."""

                    pass

                class Staticcall(ChecklistItem):
                    """STATICCALL context tests."""

                    class BanCheck(ChecklistItem):
                        """Ban check for state modifications."""

                        pass

                    class BanNoModification(ChecklistItem):
                        """Ban even without modifications."""

                        pass

                    class SubCalls(ChecklistItem):
                        """Sub-calls verification."""

                        pass

                class Delegatecall(ChecklistItem):
                    """DELEGATECALL context."""

                    pass

                    class Storage(ChecklistItem):
                        """DELEGATECALL storage modification."""

                        pass

                    class Balance(ChecklistItem):
                        """DELEGATECALL balance modification."""

                        pass

                    class Code(ChecklistItem):
                        """DELEGATECALL code modification."""

                        pass

                class Callcode(ChecklistItem):
                    """CALLCODE context."""

                    pass

                class Initcode(ChecklistItem):
                    """Initcode execution tests."""

                    class Behavior(ChecklistItem):
                        """Initcode behavior."""

                        pass

                        class Tx(ChecklistItem):
                            """Initcode from transaction."""

                            pass

                        class Opcode(ChecklistItem):
                            """Initcode from opcode."""

                            pass

                    class Reentry(ChecklistItem):
                        """Initcode re-entry."""

                        pass

                class SetCode(ChecklistItem):
                    """Set-code delegated account."""

                    pass

                class TxContext(ChecklistItem):
                    """Transaction context dependent."""

                    pass

                class BlockContext(ChecklistItem):
                    """Block context dependent."""

                    pass

            class ReturnData(ChecklistItem):
                """Return data tests."""

                class Buffer(ChecklistItem):
                    """Return buffer tests."""

                    class Current(ChecklistItem):
                        """Return buffer at current call context."""

                        pass

                    class Parent(ChecklistItem):
                        """Return buffer at parent call context."""

                        pass

            class GasUsage(ChecklistItem):
                """Gas usage tests."""

                class Normal(ChecklistItem):
                    """Normal operation gas usage."""

                    pass

                class MemoryExpansion(ChecklistItem):
                    """Memory expansion gas usage."""

                    pass

                class OutOfGasExecution(ChecklistItem):
                    """Out-of-gas due to opcode inputs."""

                    pass

                class OutOfGasMemory(ChecklistItem):
                    """Out-of-gas due to memory expansion."""

                    pass

                class OrderOfOperations(ChecklistItem):
                    """Order of operations tests."""

                    class Exact(ChecklistItem):
                        """Exact gas required."""

                        pass

                    class Oog(ChecklistItem):
                        """Out-of-gas with 1 gas difference."""

                        pass

            class Terminating(ChecklistItem):
                """Terminating opcode tests."""

                class Scenarios(ChecklistItem):
                    """Termination scenarios."""

                    class TopLevel(ChecklistItem):
                        """Top-level call termination."""

                        pass

                    class SubLevel(ChecklistItem):
                        """Sub-level call termination."""

                        pass

                    class Initcode(ChecklistItem):
                        """Initcode termination."""

                        pass

                class Rollback(ChecklistItem):
                    """Rollback tests."""

                    class Balance(ChecklistItem):
                        """Balance changes rollback."""

                        pass

                    class Storage(ChecklistItem):
                        """Storage changes rollback."""

                        pass

                    class Contracts(ChecklistItem):
                        """Contract creations rollback."""

                        pass

                    class Nonce(ChecklistItem):
                        """Nonce increments rollback."""

                        pass

                    class Logs(ChecklistItem):
                        """Log events rollback."""

                        pass

            class OutOfBounds(ChecklistItem):
                """Out-of-bounds checks."""

                class Verify(ChecklistItem):
                    """Verification tests."""

                    class Max(ChecklistItem):
                        """Max value for each parameter."""

                        pass

                    class MaxPlusOne(ChecklistItem):
                        """Max value + 1 for each parameter."""

                        pass

            class ExceptionalAbort(ChecklistItem):
                """Exceptional abort conditions."""

                pass

            class DataPortion(ChecklistItem):
                """Data portion tests."""

                class AllZeros(ChecklistItem):
                    """All zeros data portion."""

                    pass

                class MaxValue(ChecklistItem):
                    """Max value data portion."""

                    pass

                class Jump(ChecklistItem):
                    """Jump into the data portion."""

                    pass

            class ContractCreation(ChecklistItem):
                """Contract creation tests."""

                class Address(ChecklistItem):
                    """Address calculation."""

                    pass

                class Failure(ChecklistItem):
                    """Creation failure tests."""

                    class Oog(ChecklistItem):
                        """Out-of-gas failure."""

                        pass

                    class InsufficientValue(ChecklistItem):
                        """Insufficient value failure."""

                        pass

                    class Collision(ChecklistItem):
                        """Address collision failure."""

                        pass

                class Recursive(ChecklistItem):
                    """Recursive contract creation."""

                    pass

            class ForkTransition(ChecklistItem):
                """Fork transition tests."""

                class Invalid(ChecklistItem):
                    """Invalid before/after fork."""

                    pass

                class At(ChecklistItem):
                    """Behavior at transition block."""

                    pass

    class Precompile(ChecklistItem):
        """New precompile checklist items."""

        class Test(ChecklistItem):
            """Test vectors for new precompile."""

            class CallContexts(ChecklistItem):
                """Call context tests."""

                class Normal(ChecklistItem):
                    """CALL context."""

                    pass

                class Delegate(ChecklistItem):
                    """DELEGATECALL context."""

                    pass

                class Static(ChecklistItem):
                    """STATICCALL context."""

                    pass

                class Callcode(ChecklistItem):
                    """CALLCODE context."""

                    pass

                class TxEntry(ChecklistItem):
                    """Transaction entry-point."""

                    pass

                class Initcode(ChecklistItem):
                    """Initcode call tests."""

                    class CREATE(ChecklistItem, override_name="CREATE"):
                        """Call from CREATE/CREATE2 initcode."""

                        pass

                    class Tx(ChecklistItem):
                        """Call from transaction initcode."""

                        pass

                class SetCode(ChecklistItem):
                    """Set-code delegated address."""

                    pass

            class Inputs(ChecklistItem):
                """Input tests."""

                class Valid(ChecklistItem):
                    """Valid inputs."""

                    class Boundary(ChecklistItem):
                        """Valid boundary values."""

                        pass

                    class Crypto(ChecklistItem):
                        """Valid cryptographic inputs."""

                        pass

                class AllZeros(ChecklistItem):
                    """All zeros input."""

                    pass

                class MaxValues(ChecklistItem):
                    """Max values input."""

                    pass

                class Invalid(ChecklistItem):
                    """Invalid inputs."""

                    class Crypto(ChecklistItem):
                        """Invalid cryptographic inputs."""

                        pass

                    class Corrupted(ChecklistItem):
                        """Corrupted inputs."""

                        pass

            class ValueTransfer(ChecklistItem):
                """Value transfer tests."""

                class Fee(ChecklistItem):
                    """Fee-based precompile tests."""

                    class Under(ChecklistItem):
                        """Under required fee."""

                        pass

                    class Exact(ChecklistItem):
                        """Exact required fee."""

                        pass

                    class Over(ChecklistItem):
                        """Over required fee."""

                        pass

                class NoFee(ChecklistItem):
                    """No-fee precompile."""

                    pass

            class OutOfBounds(ChecklistItem):
                """Out-of-bounds checks."""

                class Max(ChecklistItem):
                    """Max value for each input."""

                    pass

                class MaxPlusOne(ChecklistItem):
                    """Max value + 1 for each input."""

                    pass

            class InputLengths(ChecklistItem):
                """Input length tests."""

                class Zero(ChecklistItem):
                    """Zero-length calldata."""

                    pass

                class Static(ChecklistItem):
                    """Static input length tests."""

                    class Correct(ChecklistItem):
                        """Correct static-length calldata."""

                        pass

                    class TooShort(ChecklistItem):
                        """Calldata too short."""

                        pass

                    class TooLong(ChecklistItem):
                        """Calldata too long."""

                        pass

                class Dynamic(ChecklistItem):
                    """Dynamic input length tests."""

                    class Valid(ChecklistItem):
                        """Valid dynamic lengths."""

                        pass

                    class TooShort(ChecklistItem):
                        """Calldata too short."""

                        pass

                    class TooLong(ChecklistItem):
                        """Calldata too long."""

                        pass

            class GasUsage(ChecklistItem):
                """Gas usage tests."""

                class Constant(ChecklistItem):
                    """Constant gas cost tests."""

                    class Exact(ChecklistItem):
                        """Exact gas consumption."""

                        pass

                    class Oog(ChecklistItem):
                        """Out-of-gas error."""

                        pass

                class Dynamic(ChecklistItem):
                    """Dynamic gas cost tests."""

                    class Exact(ChecklistItem):
                        """Exact gas consumption."""

                        pass

                    class Oog(ChecklistItem):
                        """Out-of-gas error."""

                        pass

            class ExcessiveGasUsage(ChecklistItem):
                """Excessive gas usage."""

                pass

            class ForkTransition(ChecklistItem):
                """Fork transition tests."""

                class Before(ChecklistItem):
                    """Before fork activation tests."""

                    class InvalidInput(ChecklistItem):
                        """Invalid input call."""

                        pass

                    class ZeroGas(ChecklistItem):
                        """Zero-gas call."""

                        pass

                    class Cold(ChecklistItem):
                        """Cold precompile address."""

                        pass

                class After(ChecklistItem):
                    """After fork activation tests."""

                    class Warm(ChecklistItem):
                        """Warm precompile address."""

                        pass

    class RemovedPrecompile(ChecklistItem):
        """Removed precompile checklist items."""

        class Test(ChecklistItem):
            """Test vectors for removed precompile."""

            class ForkTransition(ChecklistItem):
                """Fork transition tests."""

                class Operational(ChecklistItem):
                    """Precompile operation on fork activation."""

                    pass

                class Before(ChecklistItem):
                    """Before fork tests."""

                    class Warm(ChecklistItem):
                        """Warm precompile address."""

                        pass

                class After(ChecklistItem):
                    """After fork tests."""

                    class Cold(ChecklistItem):
                        """Cold precompile address."""

                        pass

    class SystemContract(ChecklistItem):
        """New system contract checklist items."""

        class Test(ChecklistItem):
            """Test vectors for new system contract."""

            class CallContexts(ChecklistItem):
                """Call context tests."""

                class Normal(ChecklistItem):
                    """CALL context."""

                    pass

                class Delegate(ChecklistItem):
                    """DELEGATECALL context."""

                    pass

                class Static(ChecklistItem):
                    """STATICCALL context."""

                    pass

                class Callcode(ChecklistItem):
                    """CALLCODE context."""

                    pass

                class TxEntry(ChecklistItem):
                    """Transaction entry-point."""

                    pass

                class Initcode(ChecklistItem):
                    """Initcode call tests."""

                    class CREATE(ChecklistItem, override_name="CREATE"):
                        """Call from CREATE/CREATE2 initcode."""

                        pass

                    class Tx(ChecklistItem):
                        """Call from transaction initcode."""

                        pass

                class SetCode(ChecklistItem):
                    """Set-code delegated address."""

                    pass

            class Inputs(ChecklistItem):
                """Input tests."""

                class Valid(ChecklistItem):
                    """Valid inputs."""

                    pass

                class Boundary(ChecklistItem):
                    """Boundary values."""

                    pass

                class AllZeros(ChecklistItem):
                    """All zeros input."""

                    pass

                class MaxValues(ChecklistItem):
                    """Max values input."""

                    pass

                class Invalid(ChecklistItem):
                    """Invalid inputs."""

                    class Checks(ChecklistItem):
                        """Invalid validity checks."""

                        pass

                    class Crypto(ChecklistItem):
                        """Invalid cryptographic inputs."""

                        pass

                    class Corrupted(ChecklistItem):
                        """Corrupted inputs."""

                        pass

            class ValueTransfer(ChecklistItem):
                """Value transfer tests."""

                class Fee(ChecklistItem):
                    """Fee-based system contract tests."""

                    class Under(ChecklistItem):
                        """Under required fee."""

                        pass

                    class Exact(ChecklistItem):
                        """Exact required fee."""

                        pass

                    class Over(ChecklistItem):
                        """Over required fee."""

                        pass

                class NoFee(ChecklistItem):
                    """No-fee system contract."""

                    pass

            class OutOfBounds(ChecklistItem):
                """Out-of-bounds checks."""

                class Max(ChecklistItem):
                    """Max value for each input."""

                    pass

                class MaxPlusOne(ChecklistItem):
                    """Max value + 1 for each input."""

                    pass

            class InputLengths(ChecklistItem):
                """Input length tests."""

                class Zero(ChecklistItem):
                    """Zero-length calldata."""

                    pass

                class Static(ChecklistItem):
                    """Static input length tests."""

                    class Correct(ChecklistItem):
                        """Correct static-length calldata."""

                        pass

                    class TooShort(ChecklistItem):
                        """Calldata too short."""

                        pass

                    class TooLong(ChecklistItem):
                        """Calldata too long."""

                        pass

                class Dynamic(ChecklistItem):
                    """Dynamic input length tests."""

                    class Valid(ChecklistItem):
                        """Valid dynamic lengths."""

                        pass

                    class TooShort(ChecklistItem):
                        """Calldata too short."""

                        pass

                    class TooLong(ChecklistItem):
                        """Calldata too long."""

                        pass

            class GasUsage(ChecklistItem):
                """Gas usage tests."""

                class Constant(ChecklistItem):
                    """Constant gas cost tests."""

                    class Exact(ChecklistItem):
                        """Exact gas consumption."""

                        pass

                    class Oog(ChecklistItem):
                        """Out-of-gas error."""

                        pass

                class Dynamic(ChecklistItem):
                    """Dynamic gas cost tests."""

                    class Exact(ChecklistItem):
                        """Exact gas consumption."""

                        pass

                    class Oog(ChecklistItem):
                        """Out-of-gas error."""

                        pass

            class ExcessiveGas(ChecklistItem):
                """Excessive gas tests."""

                class BlockGas(ChecklistItem):
                    """Exhaust block gas limit."""

                    pass

                class SystemCall(ChecklistItem):
                    """Excessive gas on system call."""

                    pass

            class Deployment(ChecklistItem):
                """Deployment tests."""

                class Missing(ChecklistItem):
                    """Missing system contract."""

                    pass

                class Address(ChecklistItem):
                    """Deployment address verification."""

                    pass

            class ContractVariations(ChecklistItem):
                """Contract variation tests."""

                class Networks(ChecklistItem):
                    """Different network variations."""

                    pass

            class ContractSubstitution(ChecklistItem):
                """Contract substitution tests."""

                class ReturnLengths(ChecklistItem):
                    """Modified return value lengths."""

                    pass

                class Logs(ChecklistItem):
                    """Modified logs."""

                    pass

                class RaisesException(ChecklistItem, override_name="exception"):
                    """Modified to cause exception."""

                    pass

                class GasLimitSuccess(ChecklistItem):
                    """30M gas consumption success."""

                    pass

                class GasLimitFailure(ChecklistItem):
                    """30M+1 gas consumption failure."""

                    pass

            class ForkTransition(ChecklistItem):
                """Fork transition tests."""

                class CallBeforeFork(ChecklistItem):
                    """Call system contract before fork."""

                    pass

    class TransactionType(ChecklistItem):
        """New transaction type checklist items."""

        class Test(ChecklistItem):
            """Test vectors for new transaction type."""

            class IntrinsicValidity(ChecklistItem):
                """Intrinsic validity tests."""

                class GasLimit(ChecklistItem):
                    """Gas limit tests."""

                    class Exact(ChecklistItem):
                        """Exact intrinsic gas."""

                        pass

                    class Insufficient(ChecklistItem):
                        """Insufficient gas."""

                        pass

                class MaxFee(ChecklistItem):
                    """Max fee tests."""

                    class MaxPriorityLowerThanMaxFee(ChecklistItem):
                        """Max priority < max fee."""

                        pass

                    class MaxPriorityEqualToMaxFee(ChecklistItem):
                        """Max priority == max fee."""

                        pass

                    class BaseLower(ChecklistItem):
                        """Max fee < base fee."""

                        pass

                    class BaseEqual(ChecklistItem):
                        """Max fee == base fee."""

                        pass

                class ChainId(ChecklistItem):
                    """Chain ID validation."""

                    pass

                class NonceMinusOne(ChecklistItem):
                    """Nonce == sender.nonce - 1."""

                    pass

                class NoncePlusOne(ChecklistItem):
                    """Nonce == sender.nonce + 1."""

                    pass

                class NonceExact(ChecklistItem):
                    """Nonce == sender.nonce."""

                    pass

                class To(ChecklistItem):
                    """To address validation."""

                    pass

                class ValueNonZeroInsufficientBalance(ChecklistItem):
                    """Non-zero value with insufficient balance."""

                    pass

                class ValueNonZeroSufficientBalance(ChecklistItem):
                    """Non-zero value with sufficient balance."""

                    pass

                class ValueZeroInsufficientBalance(ChecklistItem):
                    """Zero value with insufficient balance."""

                    pass

                class ValueZeroSufficientBalance(ChecklistItem):
                    """Zero value with sufficient balance."""

                    pass

                class DataFloorAboveIntrinsicGasCost(ChecklistItem):
                    """Data floor cost above intrinsic gas."""

                    pass

            class Signature(ChecklistItem):
                """Signature tests."""

                class Invalid(ChecklistItem):
                    """Invalid signature tests."""

                    class FieldOutsideCurve(ChecklistItem):
                        """Field outside curve."""

                        pass

                    class V(ChecklistItem):
                        """Invalid V values."""

                        class Two(ChecklistItem, override_name="2"):
                            """V = 2."""

                            pass

                        class TwentySeven(ChecklistItem, override_name="27"):
                            """V = 27."""

                            pass

                        class TwentyEight(ChecklistItem, override_name="28"):
                            """V = 28."""

                            pass

                        class ThirtyFive(ChecklistItem, override_name="35"):
                            """V = 35."""

                            pass

                        class ThirtySix(ChecklistItem, override_name="36"):
                            """V = 36."""

                            pass

                        class Max(ChecklistItem):
                            """V = 2**8-1."""

                            pass

                    class R(ChecklistItem):
                        """Invalid R values."""

                        class Zero(ChecklistItem, override_name="0"):
                            """R = 0."""

                            pass

                        class Secp256k1nMinusOne(ChecklistItem):
                            """R = SECP256K1N-1."""

                            pass

                        class Secp256k1n(ChecklistItem):
                            """R = SECP256K1N."""

                            pass

                        class Secp256k1nPlusOne(ChecklistItem):
                            """R = SECP256K1N+1."""

                            pass

                        class MaxMinusOne(ChecklistItem):
                            """R = 2**256-1."""

                            pass

                        class Max(ChecklistItem):
                            """R = 2**256."""

                            pass

                    class S(ChecklistItem):
                        """Invalid S values."""

                        class Zero(ChecklistItem, override_name="0"):
                            """S = 0."""

                            pass

                        class Secp256k1nHalfMinusOne(ChecklistItem):
                            """S = SECP256K1N//2-1."""

                            pass

                        class Secp256k1nHalf(ChecklistItem):
                            """S = SECP256K1N//2."""

                            pass

                        class Secp256k1nHalfPlusOne(ChecklistItem):
                            """S = SECP256K1N//2+1."""

                            pass

                        class Secp256k1nMinusOne(ChecklistItem):
                            """S = SECP256K1N-1."""

                            pass

                        class Secp256k1n(ChecklistItem):
                            """S = SECP256K1N."""

                            pass

                        class Secp256k1nPlusOne(ChecklistItem):
                            """S = SECP256K1N+1."""

                            pass

                        class MaxMinusOne(ChecklistItem):
                            """S = 2**256-1."""

                            pass

                        class Max(ChecklistItem):
                            """S = 2**256."""

                            pass

                        class Complement(ChecklistItem):
                            """S = SECP256K1N - S."""

                            pass

            class TxScopedAttributes(ChecklistItem):
                """Transaction-scoped attributes."""

                class Read(ChecklistItem):
                    """Read attributes from EVM."""

                    pass

                class OlderTxTypes(ChecklistItem):
                    """Attributes on older tx types."""

                    pass

                class Persistent(ChecklistItem):
                    """Persistent values."""

                    class Throughout(ChecklistItem):
                        """Persist throughout transaction."""

                        pass

                    class Reset(ChecklistItem):
                        """Reset on subsequent transactions."""

                        pass

            class Encoding(ChecklistItem):
                """Encoding tests."""

                class FieldSizes(ChecklistItem):
                    """Field size tests."""

                    class LeadingZero(ChecklistItem):
                        """Add leading zero byte."""

                        pass

                    class RemoveByte(ChecklistItem):
                        """Remove single byte."""

                        pass

                class ListField(ChecklistItem):
                    """List field tests."""

                    class Zero(ChecklistItem):
                        """Zero-element list."""

                        pass

                    class Max(ChecklistItem):
                        """Max count list."""

                        pass

                    class MaxPlusOne(ChecklistItem):
                        """Max count plus one."""

                        pass

                class MissingFields(ChecklistItem):
                    """Missing fields."""

                    pass

                class ExtraFields(ChecklistItem):
                    """Extra fields."""

                    pass

                class Truncated(ChecklistItem):
                    """Truncated serialization."""

                    pass

                class ExtraBytes(ChecklistItem):
                    """Extra bytes in serialization."""

                    pass

                class NewTypes(ChecklistItem):
                    """New type encoding tests."""

                    class IncorrectEncoding(ChecklistItem):
                        """Incorrect encoding."""

                        pass

            class OutOfBounds(ChecklistItem):
                """Out-of-bounds checks."""

                class Max(ChecklistItem):
                    """Max value for each field."""

                    pass

                class MaxPlusOne(ChecklistItem):
                    """Max value + 1 for each field."""

                    pass

            class ContractCreation(ChecklistItem):
                """Contract creation with new tx type."""

                pass

            class SenderAccount(ChecklistItem):
                """Sender account modifications."""

                class Nonce(ChecklistItem):
                    """Nonce increment."""

                    pass

                class Balance(ChecklistItem):
                    """Balance reduction."""

                    pass

            class BlockInteractions(ChecklistItem):
                """Block level interactions."""

                class SingleTx(ChecklistItem):
                    """Single transaction in block."""

                    class Invalid(ChecklistItem):
                        """Invalid gas limit."""

                        pass

                    class Valid(ChecklistItem):
                        """Valid gas limit."""

                        pass

                class LastTx(ChecklistItem):
                    """Last transaction in block."""

                    class Valid(ChecklistItem):
                        """Valid cumulative gas."""

                        pass

                    class Invalid(ChecklistItem):
                        """Invalid cumulative gas."""

                        pass

                class Eip7825(ChecklistItem):
                    """EIP-7825 gas limit tests."""

                    class Invalid(ChecklistItem):
                        """Exceeds EIP-7825 limit."""

                        pass

                    class Valid(ChecklistItem):
                        """Within EIP-7825 limit."""

                        pass

                class MixedTxs(ChecklistItem):
                    """Mixed transaction types."""

                    pass

            class ForkTransition(ChecklistItem):
                """Fork transition tests."""

                class Before(ChecklistItem):
                    """Before fork activation."""

                    pass

    class BlockHeaderField(ChecklistItem):
        """New block header field checklist items."""

        class Test(ChecklistItem):
            """Test vectors for new block header field."""

            class Genesis(ChecklistItem):
                """Genesis value test."""

                pass

            class ValueBehavior(ChecklistItem):
                """Value behavior tests."""

                class Accept(ChecklistItem):
                    """Block accepted with correct value."""

                    pass

                class Reject(ChecklistItem):
                    """Block rejected with incorrect value."""

                    pass

            class ForkTransition(ChecklistItem):
                """Fork transition tests."""

                class Initial(ChecklistItem):
                    """Initial value at fork."""

                    pass

                class Before(ChecklistItem):
                    """Before fork activation."""

                    pass

                class After(ChecklistItem):
                    """After fork activation."""

                    pass

    class BlockBodyField(ChecklistItem):
        """New block body field checklist items."""

        class Test(ChecklistItem):
            """Test vectors for new block body field."""

            class ValueBehavior(ChecklistItem):
                """Value behavior tests."""

                class Accept(ChecklistItem):
                    """Block accepted with correct value."""

                    pass

                class Reject(ChecklistItem):
                    """Block rejected with incorrect value."""

                    pass

            class ForkTransition(ChecklistItem):
                """Fork transition tests."""

                class Before(ChecklistItem):
                    """Before fork activation."""

                    pass

                class After(ChecklistItem):
                    """After fork activation."""

                    pass

    class GasCostChanges(ChecklistItem):
        """Gas cost changes checklist items."""

        class Test(ChecklistItem):
            """Test vectors for gas cost changes."""

            class GasUpdatesMeasurement(ChecklistItem):
                """Measure updated gas costs."""

                pass

            class OutOfGas(ChecklistItem):
                """Out-of-gas with new prices."""

                pass

            class ForkTransition(ChecklistItem):
                """Fork transition tests."""

                class Before(ChecklistItem):
                    """Before fork activation."""

                    pass

                class After(ChecklistItem):
                    """After fork activation."""

                    pass

    class GasRefundsChanges(ChecklistItem):
        """Gas refunds changes checklist items."""

        class Test(ChecklistItem):
            """Test vectors for gas refunds changes."""

            class RefundCalculation(ChecklistItem):
                """Refund calculation tests."""

                class Over(ChecklistItem):
                    """Refund over limit."""

                    pass

                class Exact(ChecklistItem):
                    """Refund at limit."""

                    pass

                class Under(ChecklistItem):
                    """Refund under limit."""

                    pass

            class ExceptionalAbort(ChecklistItem):
                """Exceptional abort tests."""

                class Revertable(ChecklistItem):
                    """Revertable operations."""

                    class Revert(ChecklistItem):
                        """REVERT."""

                        pass

                    class OutOfGas(ChecklistItem):
                        """Out-of-gas."""

                        pass

                    class InvalidOpcode(ChecklistItem):
                        """Invalid opcode."""

                        pass

                    class UpperRevert(ChecklistItem):
                        """Upper frame REVERT."""

                        pass

                class NonRevertable(ChecklistItem):
                    """Non-revertable operations."""

                    class Revert(ChecklistItem):
                        """REVERT at top frame."""

                        pass

                    class OutOfGas(ChecklistItem):
                        """Out-of-gas at top frame."""

                        pass

                    class InvalidOpcode(ChecklistItem):
                        """Invalid opcode at top frame."""

                        pass

            class CrossFunctional(ChecklistItem):
                """Cross-functional tests."""

                class CalldataCost(ChecklistItem):
                    """Calldata cost refunds."""

                    pass

    class BlobCountChanges(ChecklistItem):
        """Blob count changes checklist items."""

        class Test(ChecklistItem):
            """Test vectors for blob count changes."""

            class Eip4844BlobsChanges(ChecklistItem):
                """EIP-4844 blobs test updates."""

                pass

    class ExecutionLayerRequest(ChecklistItem):
        """New execution layer request checklist items."""

        class Test(ChecklistItem):
            """Test vectors for new execution layer request."""

            class CrossRequestType(ChecklistItem):
                """Cross-request-type interaction."""

                class Update(ChecklistItem):
                    """Update cross-request tests."""

                    pass

    class NewTransactionValidityConstraint(ChecklistItem):
        """New transaction validity constraint checklist items."""

        class Test(ChecklistItem):
            """Test vectors for the new validity constraint."""

            class ForkTransition(ChecklistItem):
                """Tests for the new transaction validity constraint on fork boundary."""

                class AcceptedBeforeFork(ChecklistItem):
                    """
                    Verify that a block before the activation fork is accepted even when the new
                    constraint is not met.
                    """

                    pass

                class AcceptedAfterFork(ChecklistItem):
                    """
                    Verify that a block after the activation fork is accepted when the new
                    validity constraint is met.
                    """

                    pass

                class RejectedAfterFork(ChecklistItem):
                    """
                    Verify that a block after the activation fork is rejected when the new
                    validity constraint is not met.
                    """

                    pass

    class ModifiedTransactionValidityConstraint(ChecklistItem):
        """Modified transaction validity constraint checklist items."""

        class Test(ChecklistItem):
            """Test vectors for the modified validity constraint."""

            class ForkTransition(ChecklistItem):
                """Tests for the modified transaction validity constraint on fork boundary."""

                class AcceptedBeforeFork(ChecklistItem):
                    """
                    Verify that a block before the activation fork is accepted when the existing
                    constraint is met and, ideally, the new constraint is not met.
                    """

                    pass

                class RejectedBeforeFork(ChecklistItem):
                    """
                    Verify that a block before the activation fork is rejected when the existing
                    constraint is not met and, ideally, the new constraint is met.
                    """

                    pass

                class AcceptedAfterFork(ChecklistItem):
                    """
                    Verify that a block after the activation fork is accepted when the new
                    validity constraint is met.
                    """

                    pass

                class RejectedAfterFork(ChecklistItem):
                    """
                    Verify that a block after the activation fork is rejected when the new
                    validity constraint is not met.
                    """

                    pass
