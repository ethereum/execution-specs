from .instructions import add, push1, sstore

ADD = 0x01
PUSH1 = 0x60
SSTORE = 0x55

op_to_func = {
    ADD: add,
    SSTORE: sstore,
    PUSH1: push1,
}
