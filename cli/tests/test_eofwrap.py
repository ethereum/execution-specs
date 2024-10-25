"""
Tests for the eofwrap module and click CLI.
"""
import pytest

from ethereum_test_base_types.conversions import to_hex
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types.eof.v1 import Container

from ..eofwrap import wrap_code


@pytest.mark.parametrize(
    "code,result",
    [
        [Op.STOP, Container.Code(Op.STOP)],
        [Op.RETURN(0, 0), Container.Code(Op.RETURN(0, 0))],
        [Op.REVERT(0, 0), Container.Code(Op.REVERT(0, 0))],
        [Op.INVALID, Container.Code(Op.INVALID)],
        [Op.PUSH1, Container.Code(Op.PUSH1[0] + Op.STOP)],
        [Op.PUSH1[0], Container.Code(Op.PUSH1[0] + Op.STOP)],
        [Op.PUSH1[0] + Op.STOP, Container.Code(Op.PUSH1[0] + Op.STOP)],
        [Op.STOP + Op.STOP, Container.Code(Op.STOP)],
        [Op.RETURN(0, 0) + Op.STOP, Container.Code(Op.RETURN(0, 0))],
        [Op.REVERT(0, 0) + Op.STOP, Container.Code(Op.REVERT(0, 0))],
        [Op.INVALID + Op.STOP, Container.Code(Op.INVALID)],
        [Op.ADDRESS, Container.Code(Op.ADDRESS + Op.STOP)],
        [Op.ADDRESS + Op.STOP, Container.Code(Op.ADDRESS + Op.STOP)],
        [Op.ADDRESS + Op.RETURN(0, 0), Container.Code(Op.ADDRESS + Op.RETURN(0, 0))],
        [Op.ADDRESS + Op.REVERT(0, 0), Container.Code(Op.ADDRESS + Op.REVERT(0, 0))],
        [Op.ADDRESS + Op.INVALID, Container.Code(Op.ADDRESS + Op.INVALID)],
        [Op.ADDRESS + Op.STOP + Op.STOP, Container.Code(Op.ADDRESS + Op.STOP)],
        [Op.ADDRESS + Op.RETURN(0, 0) + Op.STOP, Container.Code(Op.ADDRESS + Op.RETURN(0, 0))],
        [Op.ADDRESS + Op.REVERT(0, 0) + Op.STOP, Container.Code(Op.ADDRESS + Op.REVERT(0, 0))],
        [Op.ADDRESS + Op.INVALID + Op.STOP, Container.Code(Op.ADDRESS + Op.INVALID)],
        [Op.GAS + Op.STOP, Container.Code(Op.GAS + Op.STOP)],
        [Op.GAS + Op.RETURN(0, 0), Container.Code(Op.GAS + Op.RETURN(0, 0))],
        [Op.GAS + Op.REVERT(0, 0), Container.Code(Op.GAS + Op.REVERT(0, 0))],
        [Op.GAS + Op.INVALID, Container.Code(Op.GAS + Op.INVALID)],
        [Op.RJUMPV[1, 2, 3], Container.Code(Op.RJUMPV[1, 2, 3] + Op.STOP)],
        [Op.RJUMPV, Container.Code(Op.RJUMPV + Op.STOP)],
        [
            Op.RJUMPV[-1, 0x7FFF, -0x7FFF],
            Container.Code(Op.RJUMPV[-1, 0x7FFF, -0x7FFF] + Op.STOP),
        ],
    ],
    ids=lambda param: to_hex(param),
)
def test_wrap_code(code, result):
    """
    Tests for the EOF wrapping logic and heuristics
    """
    assert wrap_code(bytes(code)) == result
