
=============== ========== ================ ===========================================================
**TYPE**        **Empty**   **Length**      **Format description**
``VALUE``       0x00        Any*            0x prefixed hex up to 32 bytes long with no leading zeros.
``BYTES``       0x          Any*            0x prefixed bytes of any length
``HASH8``       0x00...00   Fixed 8         0x prefixed bytes of length 8
``HASH20``      0x00...00   Fixed 20        0x prefixed bytes of length 20
``HASH32``      0x00...00   Fixed 32        0x prefixed bytes of length 32
``HASH256``     0x00...00   Fixed 256       0x prefixed bytes of length 256
=============== ========== ================ ===========================================================

* Size can be limited by the meaning of field in tests. (like gasLimit ceil, tx signature v - value)