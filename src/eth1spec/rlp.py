verbose = False
debug = False


# main functions for encoding (RLP) and decoding (RLP_inv)
def encode(x):
    if verbose:
        print("RLP(", x, ")", "type: ", type(x))
    if type(x) in {bytearray, bytes}:
        return R_b(x)
    elif type(x) == int:
        return encode(BE(x))
    else:  # list
        return R_l(x)


# binary encoding/decoding
def R_b(x):
    if verbose:
        print("R_b(", x, ")")
    if len(x) == 1 and x[0] < 128:
        return x  # bytearray([x[0] + 0x80])
    elif len(x) < 56:
        return bytearray([128 + len(x)]) + x
    else:
        return bytearray([183 + len(BE(len(x)))]) + BE(len(x)) + x


# int to big-endian byte array
def BE(x):
    if verbose:
        print("BE(", x, ")")
    if x == 0:
        return bytearray([])
    ret = bytearray([])
    while x > 0:
        ret = bytearray([x % 256]) + ret
        x = x // 256
    return ret


# list encoding/decoding
def R_l(x):
    if verbose:
        print("R_l(", x, ")")
    sx = s(x)
    if len(sx) < 56:
        return bytearray([192 + len(sx)]) + sx
    else:
        return bytearray([247 + len(BE(len(sx)))]) + BE(len(sx)) + sx


# for a list, recursively call RLP or RLP_inv
def s(x):
    if verbose:
        print("s(", x, ")")
    sx = bytearray([])
    for xi in x:
        sx += encode(xi)
    return sx


# inverses of above


def RLP_inv(b):
    if verbose:
        print("RLP_inv(", b.hex(), ")")
    if len(b) == 0:
        return bytearray([0x80])
    if b[0] < 0xC0:  # bytes
        return R_b_inv(b)
    else:
        return R_l_inv(b)


def R_b_inv(b):
    if verbose:
        print("R_b_inv(", b.hex(), ")")
    if len(b) == 1 and b[0] < 0x80:
        return b  # bytearray([b[0]-0x80])
    elif b[0] <= 0xB7:
        return b[1 : 1 + b[0] - 0x80]
    else:
        len_BElenx = b[0] - 183
        lenx = BE_inv(b[1 : len_BElenx + 1])  # TODO lenx unused
        return b[len_BElenx + 1 : len_BElenx + 1 + lenx]


def BE_inv(b):
    if verbose:
        print("BE_inv(", b.hex(), ")")
    x = 0
    for n in range(len(b)):
        # x+=b[n]*2**(len(b)-1-n)
        x += b[n] * 2 ** (8 * (len(b) - 1 - n))
    return x


def R_l_inv(b):
    if verbose:
        print("R_l_inv(", b.hex(), ")")
    if b[0] <= 0xF7:
        lensx = b[0] - 0xC0
        sx = b[1 : 1 + lensx]
    else:
        len_lensx = b[0] - 247
        lensx = BE_inv(b[1 : 1 + len_lensx])
        sx = b[1 + len_lensx : 1 + len_lensx + lensx]
    return s_inv(sx)


def s_inv(b):
    if verbose:
        print("s_inv(", b.hex(), ")")
    x = []
    i = 0
    len_ = len(b)
    while i < len_:
        len_cur, len_len_cur = decode_length(b[i:])
        x += [RLP_inv(b[i : i + len_len_cur + len_cur])]
        i += len_cur + len_len_cur
        if debug:
            print("  s_inv() returning", x)
    if debug:
        print("  s_inv() returning", x)
    return x


# this is a helper function not described in the spec
# but the spec does not discuss the inverse to he RLP function, so never has the opportunity to discuss this
# returns the length of an encoded rlp object
def decode_length(b):
    if verbose:
        print("length_inv(", b.hex(), ")")
    if len(b) == 0:
        return 0, 0  # TODO: this may be an error
    length_length = 0
    first_rlp_byte = b[0]
    if first_rlp_byte < 0x80:
        rlp_length = 1
        return rlp_length, length_length
    elif first_rlp_byte <= 0xB7:
        rlp_length = first_rlp_byte - 0x80
    elif first_rlp_byte <= 0xBF:
        length_length = first_rlp_byte - 0xB7
        rlp_length = BE_inv(b[1 : 1 + length_length])
    elif first_rlp_byte <= 0xF7:
        rlp_length = first_rlp_byte - 0xC0
    elif first_rlp_byte <= 0xBF:
        length_length = first_rlp_byte - 0xB7
        rlp_length = BE_inv(b[1 : 1 + length_length])
    return rlp_length, 1 + length_length
