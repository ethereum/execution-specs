"""
Code object that is an interface to different
assembler/compiler backends.
"""


class Code(str):
    """
    Generic code object.
    """

    def assemble(self) -> bytes:
        """
        Assembles using `eas`.
        """
        return bytes()
