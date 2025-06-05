"""
Integer and array types which are used by—but not unique to—Ethereum.

[`Uint`] represents non-negative integers of arbitrary size, while subclasses
of [`FixedUnsigned`] (like [`U256`] or [`U32`]) represent non-negative integers
of particular sizes.

Similarly, [`Bytes`] represents arbitrarily long byte sequences, while
subclasses of [`FixedBytes`] (like [`Bytes0`] or [`Bytes64`]) represent
sequences containing an exact number of bytes.

[`Uint`]: ref:ethereum_types.numeric.Uint
[`FixedUnsigned`]: ref:ethereum_types.numeric.FixedUnsigned
[`U32`]: ref:ethereum_types.numeric.U32
[`U256`]: ref:ethereum_types.numeric.U256
[`Bytes`]: ref:ethereum_types.bytes.Bytes
[`FixedBytes`]: ref:ethereum_types.bytes.FixedBytes
[`Bytes0`]: ref:ethereum_types.bytes.Bytes0
[`Bytes64`]: ref:ethereum_types.bytes.Bytes64
"""

__version__ = "0.2.3"
