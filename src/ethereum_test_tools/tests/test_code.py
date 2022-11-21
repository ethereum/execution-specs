"""
Test suite for `ethereum_test.code` module.
"""

from ..code import Code, Yul


def test_code():
    """
    Test `ethereum_test.types.code`.
    """
    assert Code("").assemble() == bytes()
    assert Code("0x").assemble() == bytes()
    assert Code("0x01").assemble() == bytes.fromhex("01")
    assert Code("01").assemble() == bytes.fromhex("01")

    assert (Code("0x01") + "0x02").assemble() == bytes.fromhex("0102")
    assert ("0x01" + Code("0x02")).assemble() == bytes.fromhex("0102")
    assert ("0x01" + Code("0x02") + "0x03").assemble() == bytes.fromhex(
        "010203"
    )


def test_yul():
    assert (
        Yul(
            """
            {
                sstore(1, 2)
            }
            """
        ).assemble()
        == bytes.fromhex("6002600155")
    )

    assert (
        (
            Yul(
                """
                {
                    sstore(1, 2)
                }
                """
            )
            + "0x00"
        ).assemble()
        == bytes.fromhex("600260015500")
    )

    assert (
        (
            "0x00"
            + Yul(
                """
                {
                    sstore(1, 2)
                }
                """
            )
        ).assemble()
        == bytes.fromhex("006002600155")
    )

    assert (
        (
            Yul(
                """
                {
                    sstore(1, 2)
                }
                """
            )
            + Yul(
                """
                {
                    sstore(3, 4)
                }
                """
            )
        ).assemble()
        == bytes.fromhex("60026001556004600355")
    )

    long_code = (
        "{\n"
        + "\n".join(["sstore({0}, {0})".format(i) for i in range(5000)])
        + "\n}"
    )

    expected_bytecode = bytes()
    for i in range(5000):
        if i < 256:
            b = bytes.fromhex("60") + i.to_bytes(1, "big")
        else:
            b = bytes.fromhex("61") + i.to_bytes(2, "big")
        expected_bytecode += b
        # solc 0.8.7+ uses DUP1 here to optimize
        expected_bytecode += bytes.fromhex("80")
        expected_bytecode += bytes.fromhex("55")

    assert Yul(long_code).assemble() == expected_bytecode
