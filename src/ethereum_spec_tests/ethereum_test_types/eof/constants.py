"""
EVM Object Format generic constants.
Applicable to all EOF versions.
"""

EOF_MAGIC = b"\xef\x00"
"""
The second byte found on every EOF formatted contract, which was chosen to
avoid clashes with three contracts which were deployed on Mainnet.
"""
EOF_HEADER_TERMINATOR = b"\x00"
"""
Byte that terminates the header of the EOF format.
"""
LATEST_EOF_VERSION = 1
"""
Latest existing EOF version.
"""
VERSION_BYTE_LENGTH = 1
"""
Length of the version byte.
"""

MAX_RUNTIME_STACK_HEIGHT = 1024
"""
Maximum height of the EVM runtime operand stack.
Exceeding this value during execution will result in the stack overflow exception.
This value applies to both legacy EVM and EOF.
"""
