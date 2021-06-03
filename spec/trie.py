import rlp
import crypto

from spec import Account

verbose = False

# hex prefix encoding
def HP(x,t):
  # x is bytearray of values < 16
  # x is a byte array, will convert to a bytearray of values < 16
  # t is 0 or 1, or false or true
  if verbose: print("HP(",x,t,")")
  #x = bytes([int(d,16) for d in x.hex()])
  ret=bytearray()
  if len(x)%2==0: #ie even length
    ret.append(16*f(t))
    for i in range(0,len(x),2):
      ret.append(16*x[i]+x[i+1])
  else:
    ret.append(16*(f(t)+1)+x[0])
    for i in range(1,len(x),2):
      ret.append(16*x[i]+x[i+1])
  if debug: print("HP() returning", ret)
  return ret

def f(t):
  if t:
    return 2
  else:
    return 0

def HP_inv(bytes_):
  nibbles = ""
  odd_length = (bytes_[0]>>4)%2==1 #sixth lowest bit
  t = (bytes_[0]>>5)%2!=0 #fifth lowest bit
  if odd_length:
    nibbles += bytes_[0:1].hex()[1]
  for b in bytes_[1:]:
    nibbles += bytes([b]).hex()
  return nibbles, t

def y(J):
  yJ = {}
  for kn in J:
    kn_ = crypto.keccak256(kn)
    knprime = bytearray(2*len(kn_))
    for i in range(2*len(kn_)):
      if i%2==0: # even
        knprime[i] = kn_[i//2]//16
      else:
        knprime[i] = kn_[i//2]%16
    #print(kn.hex(),kn_.hex(),knprime.hex())
    yJ[bytes(knprime)] = J[kn]
  return yJ
  #return {bytes([int(d,16) for d in crypto.keccak256(k).hex()]):v for k,v in J.items()}

def TRIE(J):
  cJ0 = c(J,0)
  #print("cJ0",cJ0.hex())
  return crypto.keccak256(cJ0)

# node composition function
def n(J,i):
  #print("n(",i,")")
  if len(J)==0:
    return b''
  cJi = c(J,i)
  if len(cJi)<32:
    return cJi
  else:
    #print("cJi,crypto.keccak256(cJi)",cJi.hex(),crypto.keccak256(cJi).hex())
    return crypto.keccak256(cJi)

# structural composition function, used to patriciaize and merkleize a dictionary
# this function includes memoization of tree structure and hashes, as suggested in appx D.1
def c(J,i):
  #print("c(",J,i,")")
  #print("c(",i,")")

  if len(J)==0:
    return rlp.encode(b'') # note: empty storage tree has merkle root: crypto.keccak256(RLP(b'')) == 56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421
    # also, crypto.keccak256(RLP(())) == 1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347, which is the sha3Unlces hash in block header for no uncles

  I_0 = next(iter(J))   # get first key, will reuse below

  # if leaf node
  if len(J) == 1:
    leaf = J[I_0]
    if type(leaf) == Account:
      I_1 = rlp.encode((leaf.nonce, leaf.balance, leaf.storage_root, leaf.code_hash))
    else:
      #I_1 = leaf
      I_1 = rlp.encode(leaf)
      print("c() leaf",I_0.hex(),I_1.hex())
    #print(I_1.hex())
    val = rlp.encode((HP(I_0[i:],1),I_1))
    #print("leaf rlp",rlp.hex(),crypto.keccak256(rlp).hex())
    return val

  # prepare for extension node check by finding max j such that all keys I in J have the same I[i:j]
  l = I_0[:]
  j = len(l)
  for I_0 in J:
    j = min(j,len(I_0))
    l = l[:j]
    for x in range(i,j):
      if I_0[x] != l[x]:
        j = x
        l=l[:j]
        break
    if i==j:
      break

  # if extension node
  if i!=j:
    child = n(J,j)
    #print("extension,child",I_0[i:j].hex(),child.hex())
    val = rlp.encode((HP(I_0[i:j],0),child))
    #print("extension rlp",rlp.hex(),crypto.keccak256(rlp).hex())
    return val

  # otherwise branch node
  def u(j):
    #print("u(",j,")")
    #print([k.hex() for k in J.keys()])
    return n({I_0:I_1 for I_0,I_1 in J.items() if I_0[i]==j},i+1)
  v = b''
  for I_0 in J:
    if len(I_0)==i:
      v = J[I_0]
      break
  #print("v",v)
  val = rlp.encode([u(k) for k in range(16)] + [v])
  #print("branch rlp",rlp.hex(),crypto.keccak256(rlp).hex())
  return rlp
