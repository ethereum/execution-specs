from coincurve.ecdsa import deserialize_recoverable, recover
from coincurve.keys import PublicKey

import coincurve
import sha3

def keccak256(bytes_):
  return sha3.keccak_256(bytes_).digest()

def keccak512(bytes_):
  return sha3.keccak_512(bytes_).digest()

def secp256k1sign(msgbytes_,privkey):
  pass

def secp256k1recover(r,s,v,msg_hash):
  sig = bytearray([0]*65)
  sig[32-len(r):32] = r
  sig[64-len(s):64] = s
  sig[64] = v
  sig = bytes(sig)
  pub = coincurve.PublicKey.from_signature_and_message(sig,msg_hash,hasher=None)
  pub = pub.format(compressed=False)[1:]
  return pub
