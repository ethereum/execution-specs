"""
Where code can be jumped to, against code the framework assembles.

The framework assembles code from a list of instructions, so the test
knows where each one starts. A `JUMPDEST` byte is a jump destination
exactly where it starts an instruction, and never inside the data of a
`PUSH`.
"""

from typing import List, Tuple

from ethereum_types.bytes import Bytes
from execution_testing import Bytecode, Op
from hypothesis import given
from hypothesis import strategies as st

from ethereum_spec_tools.forks import Hardfork

PUSHES = [getattr(Op, f"PUSH{n}") for n in range(1, 33)]
OTHER_BYTES = sorted(
    set(range(256)) - {opcode.int() for opcode in [Op.JUMPDEST, *PUSHES]}
)
# The opcodes on either side of the `PUSH` range, and the ones that carry
# an immediate the analysis does not skip.
NOT_A_PUSH = sorted(
    {PUSHES[0].int() - 1, PUSHES[-1].int() + 1}
    | {
        opcode.int()
        for opcode in Op
        if opcode.data_portion_length and opcode not in PUSHES
    }
)

# Push data that looks like instructions: a `JUMPDEST` the analysis must
# skip, and `PUSH` opcodes it must not read as the start of more data.
push_data_bytes = st.one_of(
    st.sampled_from(
        [Op.JUMPDEST.int(), Op.PUSH1.int(), Op.PUSH32.int(), 0x00]
    ),
    st.integers(0, 255),
)


@st.composite
def pushes(draw: st.DrawFn) -> Bytecode:
    """Return a `PUSH` with all of its data."""
    opcode = draw(
        st.one_of(
            st.sampled_from([PUSHES[0], PUSHES[-1]]), st.sampled_from(PUSHES)
        )
    )
    size = opcode.data_portion_length
    data = draw(st.lists(push_data_bytes, min_size=size, max_size=size))
    return opcode[bytes(data)]


@st.composite
def cut_off_pushes(draw: st.DrawFn) -> bytes:
    """Return a `PUSH` whose data the end of the code cuts short."""
    opcode = draw(st.sampled_from(PUSHES))
    size = draw(st.integers(0, opcode.data_portion_length - 1))
    data = draw(st.lists(push_data_bytes, min_size=size, max_size=size))
    return bytes(opcode) + bytes(data)


@st.composite
def code_with_jump_destinations(draw: st.DrawFn) -> Tuple[bytes, List[int]]:
    """Return code and the offsets where a `JUMPDEST` instruction starts."""
    instructions = draw(
        st.lists(
            st.one_of(
                st.just(Op.JUMPDEST),
                pushes(),
                # Every other byte is one instruction with no data, whether
                # the fork defines it or not.
                st.one_of(
                    st.sampled_from(NOT_A_PUSH), st.sampled_from(OTHER_BYTES)
                ).map(lambda byte: bytes([byte])),
            ),
            max_size=24,
        )
    )
    code = b""
    destinations = []
    for instruction in instructions:
        if instruction is Op.JUMPDEST:
            destinations.append(len(code))
        code += bytes(instruction)
    if draw(st.booleans()):
        code += draw(cut_off_pushes())
    return code, destinations


@given(code_and_destinations=code_with_jump_destinations())
def test_jump_destinations_are_the_jumpdest_instructions(
    spec: Hardfork, code_and_destinations: Tuple[bytes, List[int]]
) -> None:
    """
    The valid jump destinations of a code are the offsets where the
    framework placed a `JUMPDEST` instruction.
    """
    code, destinations = code_and_destinations
    runtime = spec.module("vm.runtime")

    valid = runtime.get_valid_jump_destinations(Bytes(code))

    assert sorted(int(offset) for offset in valid) == destinations
