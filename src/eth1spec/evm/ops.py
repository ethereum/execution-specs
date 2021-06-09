# flake8: noqa 405

from .instructions import *  # noqa 403

ADD = 0x01
PUSH1 = 0x60
SSTORE = 0x55

op_to_func = {
    ADD: add,
    SSTORE: sstore,
    PUSH1: push1,
}
