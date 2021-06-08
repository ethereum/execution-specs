#! /usr/bin/node


// Generate a test that looks at all the opcodes and identifies if any
// of them is not implemented correctly

// Directions:
//
// testOpcodesGen.js > \
//       tests/src/BlockchainTestsFiller/ValidBlocks/bcStateTests/testOpcodesFiller.yml
//
// When a new fork is added, add it to the forks array. When a fork is no
// longer relevant, remove it. Make sure that array is always sorted by time.
//
// When a new opcode is added, add it to the opcodes array like this:
// <opcode>: {
//   test: "0x<machine language code>",
//   fromFork: "<fork where first applicable>"
// },
//



// Maximum gas we're allowed to use
const gasLimit = 'F00000000000'

// "User"'s gas balance
const userBalance = 'F000000000000000'

// The forks supported by the test in order. At writing, there is no need
// to QA forks prior to Istanbul.
const forks = ["Berlin", "London"]





// Turn a byte numeric value into hex
const byte2Hex = n => n>15 ? n.toString(16) : "0"+n.toString(16)


// Turn an up to eight byte value into hex
const eightByte2Hex = n => ("0000000000000000" + n.toString(16)).slice(-16)




// The WEI balance of acct0, <256
const addr0Wei = 0x99

// WEI to send to a new contract, <256
const newContractWei = 0x3F


// The WEI amount of the transaction, <256
// For some reason this fails with insufficient funds when it is not zero
const transactWei = 0

const gasPrice = 20

const difficulty = 0x20000  // Max eight bytes



// Addresses

// Return the contract address for an opcode
const opcode2Addr = op => `0x7E57C0DE000000000000000000000000000000${byte2Hex(op)}`

// The contract that tests all the opcode contracts
const bigTestContractAddr = "0xB1607E5700000000000000000000000000000000"

// User address
const userAddr = "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b"

// Coinbase
const coinBaseAddr = "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"


// Called contract's information
const calledContractAddr = "0xCA11ED0000000000000000000000000000000000"
const retData = "deadbeef"  // hardwired as four bytes
const storedData = "0dad"   // hardwired as two bytes
// The called contract returns the DEADBEEF, and stores 0x0DAD at
// storage location 0x0DAD.


const contractBalance = eightByte2Hex(0xFFFFFFFFFFFFFF)


const boilerPlate_Contract =
`balance: 0x${contractBalance}
      nonce: 0
      storage: {}`

const boilerPlate_Head = `


  genesisBlockHeader:
    bloom: 0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
    coinbase: ${coinBaseAddr.slice(2)}
    difficulty: ${difficulty}
    extraData: 0x42
    gasLimit: ${gasLimit}
    gasUsed: 0
    mixHash: 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421
    nonce: 0x0102030405060708
    number: 0
    parentHash: 0x0000000000000000000000000000000000000000000000000000000000000000
    receiptTrie: 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421
    stateRoot: 0xf99eb1626cfa6db435c0836235942d7ccaa935f1ae247d3f1c21e495685f903a
    timestamp: 0x54c98c81
    transactionsTrie: 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421
    uncleHash: 0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347
    baseFee: 10


  _info:
    comment: Generated from testOpcodesGen.js, do not edit directly

  pre:

    # The "user" account
    '${userAddr}':
      balance: ${userBalance}
      code: 0x
      nonce: 0
      storage: {}


    '0x0000000000000000000000000000000000000000':
      balance: ${addr0Wei}
      nonce: 0
      storage: {}
      code: 0x


    # A suicidal contract
    #
    # 0 PUSH1 0
    # 2 SELFDESTRUCT
    #
    # It is not trivial to check SELFDESTRUCT because the actual destruction
    # only happens after the transaction. However, the transfer of balance
    # happens immediately, so it can be checked within the same transaction
    '0x00000000000000000000000000000000000000FF':
      balance: ${addr0Wei}
      nonce: 0
      storage: {}
      code: :raw 0x6000FF

`


// Create a test for a two operand opcode, with both operands and
// the result in a single byte
const aOPb_to_ml = (a, b, op, res) => "0x" +
  `60${byte2Hex(b)}`   +    //  0 PUSH1 b
  `60${byte2Hex(a)}`   +    //  2 PUSH1 a
  `${byte2Hex(op)}`    +    //  4 op
  `60${byte2Hex(res)}` +    //  5 PUSH1 res
  "14"                 +    //  7 EQ
  "600C"               +    //  8 PUSH1 0xOC (a.k.a. 12)
  "57"                 +    // 10 JUMPI  if the result is correct
  "FD"                 +    // 11 REVERT
  "5B"                 +    // 12 JUMPDEST
  "00"                      // 13 STOP


// Create a test for a three operand opcode, with all operands and
// the result in a single byte
const abcOP_to_ml = (a, b, c, op, res) => "0x" +
  `60${byte2Hex(c)}`   +    //  0 PUSH1 c
  `60${byte2Hex(b)}`   +    //  2 PUSH1 b
  `60${byte2Hex(a)}`   +    //  4 PUSH1 a
  `${byte2Hex(op)}`    +    //  6 op
  `60${byte2Hex(res)}` +    //  7 PUSH1 res
  "14"                 +    //  9 EQ
  "600E"               +    // 10 PUSH1 0xOE (a.k.a. 14)
  "57"                 +    // 12 JUMPI  if the result is correct
  "FD"                 +    // 13 REVERT
  "5B"                 +    // 14 JUMPDEST
  "00"                      // 15 STOP


// Run an opcode, compare to a value up to eight bytes
const compare_op_8byte_ml = (op, val) => "0x" +
        "67"              +   //  0 PUSH20 <expected address>
        eightByte2Hex(val) +
        byte2Hex(op)      +   //  9 opcode
        "14"              +   // 10 EQ
        "600F"            +   // 11 PUSH1 15 (0x0F)
        "57"              +   // 13 JUMPI
        "FD"              +   // 14 REVERT (not equal)
        "5B00"                // 15 JUMPDEST, STOP



// Run an opcode, compare to a given address
const compare_op_addr_ml = (op, addr) => "0x" +
        "73"              +   //  0 PUSH20 <expected address>
        addr.slice(2)     +
        byte2Hex(op)      +   // 21 opcode
        "14"              +   // 22 EQ
        "601B"            +   // 23 PUSH1 27 (0x1B)
        "57"              +   // 25 JUMPI
        "FD"              +   // 26 REVERT (not equal)
        "5B00"                // 27 JUMPDEST, STOP


// Store a value (op+1) and then load it (op). This value can be either
// in memory (op=0x51) or storage (op=0x54)
const load_store_ml = op => "0x" +
        "60FF"            +   //  0 PUSH1 0xFF (can be any value)
        "60FF"            +   //  2 PUSH1 0xFF (same value as in PC 0)
        "6020"            +   //  4 PUSH1 0x20 (address)
        byte2Hex(op+1)    +   //  6 MSTORE / SSTORE
        "6020"            +   //  7 PUSH1 0x20 (address, same as in PC 4)
        byte2Hex(op)      +   //  9 MLOAD / SLOAD
        "14"              +   // 10 EQ
        "600F"            +   // 11 PUSH1 0x0F (addr. 15)
        "57FD"            +   // 13 JUMPI, REVERT
        "5B00"                // 15 JUMPDEST, STOP


// The machine language to check PUSH<n> opcodes
const push_n_ml = op => {
  const n = op-0x60+1   // 0x60 is PUSH1, 0x61 is PUSH2 ... 0x7F is PUSH32

  // For any value, create an n BYTE value equal to 255
  var bytes = ""
  for (var i=0; i<n-1; i++)
    bytes += "00"
  bytes += "FF"

  return "0x" +
     byte2Hex(op)          + //    0 PUSH<n> 0xFF
     bytes                 +
     "60FF"                + //  n+1 PUSH1 0xFF
     "14"                  + //  n+3 EQ
     `60${byte2Hex(n+8)}`  + //  n+4 PUSH1 n+8
     "57"                  + //  n+6 JUMPI
     "FD"                  + //  n+7 REVERT
     "5B00"                  //  n+8 JUMPDEST, STOP
}


// The machine language code to check DUP<n>
const dup_n_ml = op => {
  const n = op-0x80+1  // 0x80 is DUP1

  var pushes = ""  // PUSH1 16; PUSH1 15 ... PUSH1 1
  for(var i=16; i>0; i--)
    pushes += `60${byte2Hex(i)}`

  return "0x"             +
     pushes               +     //   0 PUSH 16-1
     byte2Hex(op)         +     //  32 DUPn
     `60${byte2Hex(n)}`   +     //  33 PUSH1 n
     "14"                 +     //  35 EQ
     `60${byte2Hex(40)}`  +     //  36 PUSH1 40
     "57"                 +     //  38 JUMPI
     "FD"                 +     //  39 REVERT
     "5B00"                     //  40 JUMPDEST, STOP

}



// The machine language code to check SWAP<n>
const swap_n_ml = op => {
  const n = op-0x90+1  // 0x90 is SWAP1

  var pushes = ""  // PUSH1 16; PUSH1 15 ... PUSH1 1
  for(var i=16; i>0; i--)
    pushes += `60${byte2Hex(i)}`

  return "0x"             +
     pushes               +     //   0 PUSH 16-1
     "60FF"               +     //  32 PUSH1 FF
     byte2Hex(op)         +     //  34 SWAPn
     `60${byte2Hex(n)}`   +     //  35 PUSH1 n
     "14"                 +     //  37 EQ
     `60${byte2Hex(42)}`  +     //  38 PUSH1 42
     "57"                 +     //  40 JUMPI
     "FD"                 +     //  41 REVERT
     "5B00"                     //  42 JUMPDEST, STOP

}



// The machine language code for OPs that don't leave an output
// we can read. Just see that the opcode doesn't cause a revert
const cant_test_ml = op => {

  // Make sure there are enough parameters
  var pushes = ""  // PUSH1 16; PUSH1 15 ... PUSH1 1
  for(var i=16; i>0; i--)
    pushes += `60${byte2Hex(i)}`

  return "0x"             +
     pushes               +     //   0 PUSH 16-1
     byte2Hex(op)         +     //  32 op
     "00"                       //  33 STOP
}



// Put values in a specific memory location. This is useful when
// creating a contract. This code is inefficient, but I'm optimizing
// for programmer time. Note that this function does not have a
// 0x prefix, because this is not a complete program.
const str2mem_ml = (str, mem) => {
    res = ''
    for (var i=0, ptr=mem; i<str.length; i+=2, ptr++) {
      res += `60${str[i]}${str[i+1]}60${byte2Hex(ptr)}53`;
    }

    return res;
}



// The opcode table. For each opcode, this table may contain:
//
// test: A test for the opcode (in machine language), this test can either
//       end with a STOP (success) or with a REVERT (failure)
// testRes: The expected result of that test, by default success
// firstFork: The first fork at which this opcode is valid (by default forks[0])
//
// If an opcode does not exist, it is assumed to be invalid in all
// forks being tested
//
// This is a variable because we're going to use loops for some repetitive
// opcodes, such as PUSH1 - PUSH32

var opcodes = {
   0x00: {    // STOP
     test: "0x00" +    // 1 STOP
             "6000" +  // 2 PUSH1 0   If stop didn't work, revert
             "6000" +  // 4 PUSH1 0
             "FD"      // 5 REVERT
   },

   // Easy three or less operand tests, with each operand and the result
   // 0 <= x < 256
   0x01: { test: aOPb_to_ml(3, 2, 0x01, 5) },   // ADD
   0x02: { test: aOPb_to_ml(3, 2, 0x02, 6) },   // MUL
   0x03: { test: aOPb_to_ml(16, 8, 0x03, 8) },  // SUB
   0x04: { test: aOPb_to_ml(16, 8, 0x04, 2) },  // DIV
   0x05: { test: aOPb_to_ml(16, 8, 0x05, 2) },  // SDIV
   0x06: { test: aOPb_to_ml(15, 4, 0x06, 3) },  // MOD
   0x07: { test: aOPb_to_ml(15, 4, 0x07, 3) },  // SMOD

   0x08: {test: abcOP_to_ml(10, 7, 3, 0x08, 2) },  // ADDMOD (10+7) % 3
   0x09: {test: abcOP_to_ml(10, 7, 3, 0x09, 1) },  // MULMOD (10*7) % 3

   0x0A: { test: aOPb_to_ml(3, 2, 0x0A, 9) },   // EXP
   0x10: { test: aOPb_to_ml(3, 2, 0x10, 0) },   // LT
   0x11: { test: aOPb_to_ml(3, 2, 0x11, 1) },   // GT
   0x12: { test: aOPb_to_ml(3, 2, 0x12, 0) },   // SLT
   0x13: { test: aOPb_to_ml(3, 2, 0x13, 1) },   // SGT
   0x14: { test: aOPb_to_ml(3, 2, 0x14, 0) },   // EQ
   0x15: { test: aOPb_to_ml(0, 2, 0x15, 1) },   // ISZERO
   0x16: { test: aOPb_to_ml(6, 3, 0x16, 2) },   // AND
   0x17: { test: aOPb_to_ml(6, 3, 0x17, 7) },   // OR
   0x18: { test: aOPb_to_ml(6, 3, 0x18, 5) },   // XOR
   0x1A: { test: aOPb_to_ml(31, 0xFF, 0x1A, 0xFF) },// BYTE, out of a 32 byte value
   0x1B: { test: aOPb_to_ml(2, 6, 0x1B, 24) },  // SHL   (6 << 2)
   0x1C: { test: aOPb_to_ml(2, 6, 0x1C, 1) },   // SHR   (6 >> 2)
   0x1D: { test: aOPb_to_ml(2, 6, 0x1D, 1) },   // SAR   (6 >> 2), shift respects neg

   // These opcodes return a byte value. They aren't mathematical operations,
   // but the code still works
   0x31: { test: aOPb_to_ml(0, 0, 0x31, addr0Wei) },     // BALANCE
   0x34: { test: aOPb_to_ml(0, 0, 0x34, transactWei) },  // CALLVALUE
   0x36: { test: aOPb_to_ml(0, 0, 0x36, 32) },           // CALLDATASIZE
   0x38: { test: aOPb_to_ml(2, 6, 0x38, 0x0E) },         // CODESIZE
   0x3A: { test: aOPb_to_ml(2, 6, 0x3A, gasPrice) },     // GASPRICE
   0x43: { test: aOPb_to_ml(2, 6, 0x43, 1) },            // NUMBER
   0x46: { test: aOPb_to_ml(2, 6, 0x46, 1) },            // CHAINID
   0x48: { test: aOPb_to_ml(2, 6, 0x48, 9),              // BASEFEE
           fromFork: 'London' },
   0x50: { test: aOPb_to_ml(2, 6, 0x50, 6) },            // POP
   0x58: { test: aOPb_to_ml(2, 6, 0x58, 4) },            // PC


   // Opcodes that can be tested against an eight byte value
   0x44: { test: compare_op_8byte_ml(0x44, difficulty)    }, // DIFFICULTY
   0x45: { test: compare_op_8byte_ml(0x45, gasLimit)      }, // GASLIMIT
   0x47: { test: compare_op_8byte_ml(0x47, contractBalance) }, // SELFBALANCE

   // Opcodes that return an address - verify it is the correct one
   0x30: { test: compare_op_addr_ml(0x30, opcode2Addr(0x30))   }, // ADDRESS
   0x32: { test: compare_op_addr_ml(0x32, userAddr)            }, // ORIGIN
   0x33: { test: compare_op_addr_ml(0x33, bigTestContractAddr) }, // CALLER
   0x41: { test: compare_op_addr_ml(0x41, coinBaseAddr) },        // COINBASE

   // Loading and storing data
   0x51: { test: load_store_ml(0x51) },      // MLOAD
   0x52: { test: load_store_ml(0x51) },      // MSTORE
   0x54: { test: load_store_ml(0x54) },      // SLOAD
   0x55: { test: load_store_ml(0x54) },      // SSTORE



   // Opcodes that we can't really test, we just run them with a bunch of
   // parameters and see they don't REVERT
   0xA0: { test: cant_test_ml(0xA0) },      // LOG0
   0xA1: { test: cant_test_ml(0xA1) },      // LOG1
   0xA2: { test: cant_test_ml(0xA2) },      // LOG2
   0xA3: { test: cant_test_ml(0xA3) },      // LOG3
   0xA4: { test: cant_test_ml(0xA4) },      // LOG4


   // Opcodes that require their own tests

   0x0B: {  // SIGN EXTEND
      test: "0x" +
         "60FF"  + //  0 PUSH 0xFF (-1 for a one byte number)
         "6000"  + //  2 PUSH 0 (to extend for a byte to a full number)
         "0B"    + //  4 SIGNEXTEND (at this point the value on the stack should be -1)
         "6001"  + //  5 PUSH 1
         "01"    + //  7 ADD        (-1 + 1 = 0)
         "600C"  + //  8 PUSH 0x0C (a.k.a. 12)
         "57"    + // 10 JUMPI (if the value is not zero)
         "00"    + // 11 STOP (if the value is zero)
         "5B"    + // 12 JUMPDEST
         "FD"      // 14 REVERT
   },



   0x19: {  // NOT
      test: "0x" +
         "60FF"  + //  0 PUSH 0xFE (-2 for a one byte number)
         "6000"  + //  2 PUSH 0 (to extend for a byte to a full number)
         "0B"    + //  4 SIGNEXTEND (value: FFFFF...E)
         "19"    + //  5 NOT        (value: 1)
         "6001"  + //  6 PUSH 1
         "14"    + //  8 EQ
         "600E"  + // 10 PUSH 0x0E (a.k.a. 14)
         "57"    + // 12 JUMPI (if the value is not zero)
         "00"    + // 13 STOP (if the value is zero)
         "5B"    + // 14 JUMPDEST
         "FD"      // 15 REVERT
   },


   0x20: {   // HASH a memory area. Verify that two segments with different
             // values hash differently
     test: "0x" +
       "6005"   +   //   0 PUSH 05
       "6000"   +   //   2 PUSH 00
       "20"     +   //   4 HASH (memory[0-5])
       "6006"   +   //   5 PUSH 05
       "6000"   +   //   7 PUSH 00
       "20"     +   //   9 HASH (memory[0-6])
       "14"     +   //  10 EQ
       "600F"   +   //  11 PUSH1 0x0F (15)
       "57"     +   //  13 JUMPI
       "00"     +   //  14 STOP (not equal)
       "5BFD"       //  15 JUMPDEST, REVERT
   },


   0x3B: {   // EXTCODESIZE
     test: "0x" +
        "73"              +   //  0 PUSH20 <address of this contract>
        opcode2Addr(0x3B).slice(2) +
        "3B"              +   // 21 EXTCODESIZE
        "38"              +   // 22 CODESIZE, should be the same
        "14"              +   // 23 EQ
        "601C"            +   // 24 PUSH1 28 (0x1C)
        "57"              +   // 26 JUMPI
        "FD"              +   // 27 REVERT (not equal)
        "5B00"                // 28 JUMPDEST, STOP
   },

   0x3F: {  // EXTCODEHASH, verify that two different contracts give different values
     test: "0x"        +
       "73"            +  //  0 PUSH20 <address of a contract>
       opcode2Addr(0x3F).slice(2) +
       "3F"            +  // 21 EXTCODEHASH
       "73"            +  // 22 PUSH20 <address of a different contract>
       bigTestContractAddr.slice(2) +
       "3F"            +  // 43 EXTCODEHASH
       "14"            +  // 44 EQ
       "6031"          +  // 45 PUSH1 49 (0x31)
       "57"            +  // 47 JUMPI
       "00"            +  // 48 STOP (numbers should not be equal)
       "5BFD"             // 49 JUMPDEST, REVERT
   },


   0x40: { // BLOCKHASH, the hash of a nearby previous block. This
           // value is random (not taken from env:), so the best I
           // can do is ensure it is consistent
     test: "0x"        +
       "6000"          +  //  0 PUSH1 0 Number of previous block
       "40"            +  //  2 BLOCKHASH
       "6000"          +  //  3 PUSH1 0 Number of previous block
       "40"            +  //  5 BLOCKHASH
       "14"            +  //  6 EQ
       "600B"          +  //  7 PUSH1 11 (0x0B)
       "57FD"          +  //  9 JUMPI, REVERT
       "5B00"             // 11 JUMPDEST, END
   },


   0x42: { // TIMESTAMP, just verify the two values are equal (because
           // they apply to the same block)
     test: "0x"        +
       "42"            +  //  0 TIMESTAMP
       "42"            +  //  1 TIMESTAMP
       "14"            +  //  2 EQ
       "6007"          +  //  3 PUSH1 7
       "57"            +  //  5 JUMPI
       "FD"            +  //  6 REVERT
       "5B00"             //  7 JUMPDEST, END
   },

   0x43: { // NUMBER, which is always block one in a state transition test
     test: "0x"        +
       "43"            +  //  0 NUMBER
       "6001"          +  //  1 PUSH1 1
       "14"            +  //  3 EQ
       "6008"          +  //  4 PUSH1 8
       "57"            +  //  6 JUMPI
       "FD"            +  //  7 REVERT
       "5B00"             //  8 JUMPDEST, END
   },

   0x53: { // MSTORE8 (bits)
     test: "0x"        +
        "60FF"            +   //  0 PUSH1 0xFF (can be any value)
        "6111FF"          +   //  2 PUSH1 0x11FF
        "6020"            +   //  5 PUSH1 0x20 (address)
        "53"              +   //  7 MSTORE8 (only the 0xFF part, as LSB)
        "6020"            +   //  8 PUSH1 0x20 (address, same as in PC 5)
        "51"              +   // 10 MLOAD (loaded as MSB)
        "60F8"            +   // 11 PUSH 0xF8
        "1C"              +   // 13 SHR
        "14"              +   // 14 EQ
        "6013"            +   // 15 PUSH1 0x13 (addr. 19)
        "57FD"            +   // 17 JUMPI, REVERT
        "5B00"                // 19 JUMPDEST, STOP
   },


   0x56: { // JUMP
     test: "0x"           +
        "6004"            +   //  0 PUSH1 0x04
        "56"              +   //  2 JUMP
        "FD"              +   //  3 REVERT
        "5B00"                //  4 JUMPDEST, STOP
   },

   0x5B: { // JUMPDEST, same test as JUMP
     test: "0x600456FD5B00"
   },


   0x57: { // JUMPI
     test: "0x"           +
        "6001"            +   //  0 PUSH1 1
        "6006"            +   //  2 PUSH1 0x06
        "57"              +   //  4 JUMPI
        "FD"              +   //  5 REVERT
        "5B"              +   //  6 JUMPDEST
        "6000"            +   //  7 PUSH1 0
        "600D"            +   //  9 PUSH1 13 (0x0D)
        "57"              +   // 11 JUMPI
        "00"              +   // 12 STOP
        "5BFD"                // 13 JUMPDEST, REVERT
   },

   0x59: { // MSIZE, memory is allocated in 64 byte chunks (0x40)
     test: "0x"        +
        "60FF"            +   //  0 PUSH1 0xFF (can be any value)
        "6020"            +   //  2 PUSH1 0x10 (address)
        "52"              +   //  4 MSTORE
        "59"              +   //  5 MSIZE
        "6040"            +   //  6 PUSH1 0x40
        "14"              +   //  8 EQ
        "600D"            +   //  9 PUSH1 0x0D (addr. 13)
        "57FD"            +   // 11 JUMPI, REVERT
        "5B00"                // 13 JUMPDEST, STOP
   },


   0x5A: { // GAS, just check the value changes
     test: "0x"        +
        "5A"            +   //  0 GAS
        "5A"            +   //  1 GAS
        "14"            +   //  2 EQ
        "6007"          +   //  3 PUSH1 7
        "5700"          +   //  5 JUMPI, STOP
        "5BFD"              //  7 JUMPDEST, REVERT
   },


   0xF0: { // CREATE, note that the created contract is automatically
           // called (so it can have a constructor)
           //
           // This code verifies that the contract is created by
           // sending it an initial balance and seeing that the contract
           // address does have that balance
     test: "0x" +
        str2mem_ml("00", 0x20)          +   // the contract "code", one byte
                                            // str2mem_ml is always five bytes per
                                            // byte written
        "6001"                          +   //  5    PUSH1 01 (contract length)
        "6020"                          +   //  7    PUSH1 20 (contract address)
        `60${byte2Hex(newContractWei)}` +   //  9    PUSH1 <Wei to send>
        "F0"                            +   // 11    CREATE
        "31"                            +   // 12    BALANCE (of the new contract)
        `60${byte2Hex(newContractWei)}` +   // 13    PUSH <Wei to send>
        "14"                            +   // 15    EQ
        "6014"                          +   // 16    PUSH1 20 (0x14)
        "57FD"                          +   // 18    JUMPI, REVERT
        "5B00"                              // 20    JUMPDEST, STOP
   },


   0xF5: { // CREATE2, note that the created contract is automatically
           // called (so it can have a constructor)
           //
           // CREATE2 generates a deterministic address, so we check it
           // by verifying it creates the contract in the expected address
     test: "0x" +
        str2mem_ml("00", 0x20)          +   // the contract "code", one byte
                                            // str2mem_ml is always five bytes per
                                            // byte written
        "60FF"                          +   //  5    PUSH1 0xFF (salt)
        "6001"                          +   //  7    PUSH1 01 (contract length)
        "6020"                          +   //  9    PUSH1 20 (contract address)
        `60${byte2Hex(newContractWei)}` +   // 11    PUSH1 <Wei to send>
        "F5"                            +   // 13    CREATE2
        "73999904ecaeacf74500f4016c718745d26d78fec3" + // 14 PUSH <expected address>
        "14"                            +   // 35    EQ
        "6028"                          +   // 36    PUSH1 40 (0x28)
        "57FD"                          +   // 38    JUMPI, REVERT
        "5B00"                              // 40    JUMPDEST, STOP
   },


   0xF1: {              // CALL
      test: "0x" +
        str2mem_ml("AABBCCDD", 0xC)  +   // Arguments to send, 4 bytes
        "6004"                    + // 20 PUSH1 4   Length of return data
        "6000"                    + // 22 PUSH1 0   Memory location for return data
        "6004"                    + // 24 PUSH1 4   Args length
        "600C"                    + // 26 PUSH1 C   Memory location of arguments
        "6000"                    + // 28 PUSH1 0   Value, Wei to send
        `73${calledContractAddr.slice(2)}` + // 30 PUSH calledContractAddr
        "5A"                      + // 51 GAS       Push the gas amount
        "F1"                      + // 52 CALL      Phew! We finally get to do a call
        "6000"                    + // 53 PUSH1 0   Memory location for return data
        "51"                      + // 55 MLOAD     Load return data
        "60E0"                    + // 56 PUSH1 224
        "1C"                      + // 57 SHR (move deadbeef to least significant)
        `63${retData}`            + // 59 PUSH4 DEADBEEF
        "14"                      + // 64 EQ
        "16"                      + // 65 AND  (successful call and got DEADBEEF)
        "6046"                    + // 66 PUSH1 70 (0x46)
        "57FD"                    + // 68 JUMPI, REVERT
        "5B00"                      // 70 JUMPDEST, STOP
   },



   0xF2: {              // CALLCODE, similar to DELEGATECALL, except
      test: "0x" +      // 1. We do need to push a value in Wei of the transfer
                        // 2. Values are not returned to memory
                        // (and some other differences in the env for the
                        // called account)
        str2mem_ml("AABBCCDD", 0xC)  +   // Arguments to send, 4 bytes
        "6004"                    + // 20 PUSH1 4   Length of return data
        "6000"                    + // 22 PUSH1 0   Memory location for return data
        "6004"                    + // 24 PUSH1 4   Args length
        "600C"                    + // 26 PUSH1 C   Memory location of arguments
        "6000"                    + // 28 PUSH1 0   Wei we're sending (zero)
        `73${calledContractAddr.slice(2)}` + // 30 PUSH calledContractAddr
        "5A"                      + // 51 GAS       Push the gas amount
        "F2"                      + // 52 CALLCODE      Phew! We finally get to do a call
        "6000"                    + // 53 PUSH1 0   Memory location for return data
        "51"                      + // 55 MLOAD     Load return data
        "60E0"                    + // 56 PUSH1 224
        "1C"                      + // 57 SHR (move deadbeef to least significant)
        `63${retData}`            + // 59 PUSH4 DEADBEEF
        "14"                      + // 64 EQ
        "16"                      + // 65 AND  (successful call and got DEADBEEF)
        `61${storedData}`         + // 66 PUSH2 DAD
        "54"                      + // 69 SLOAD  Should have DAD stored at DAD
        `61${storedData}`         + // 70 PUSH2 DAD
        "14"                      + // 73 EQ
        "16"                      + // 74 AND (also correct storage)
        "604F"                    + // 75 PUSH1 79 (0x4F)
        "57FD"                    + // 77 JUMPI, REVERT
        "5B00"                      // 79 JUMPDEST, STOP
   },


   0xF3: {              // RETURN, checked by the same program as CALL
                        // The opcode checked actually lives in
                        // calledContractAddr
      test: "0x" +
        str2mem_ml("AABBCCDD", 0xC)  +   // Arguments to send, 4 bytes
        "600460006004600C6000" +
        `73${calledContractAddr.slice(2)}` +
        `5AF160005160E01C63${retData}1416604657FD5B00`
   },


   0xF4: {              // DELEGATECALL
      test: "0x" +
        str2mem_ml("AABBCCDD", 0xC)  +   // Arguments to send, 4 bytes
        "6000"                    + // 20 PUSH1 0   Not needed, only here
                                    //              to compensate for the
                                    //              fact we don't need to
                                    //              send Value, and I am
                                    //              too lazy to recalcualte
                                    //              addresses
        "6004"                    + // 22 PUSH1 4   Length of return data
        "6000"                    + // 24 PUSH1 0   Memory location for return data
        "6004"                    + // 26 PUSH1 4   Args length
        "600C"                    + // 28 PUSH1 C   Memory location of arguments
        `73${calledContractAddr.slice(2)}` + // 30 PUSH calledContractAddr
        "5A"                      + // 51 GAS       Push the gas amount
        "F4"                      + // 52 DELEGATECALL      Phew! We finally get to do a call
        "6000"                    + // 53 PUSH1 0   Memory location for return data
        "51"                      + // 55 MLOAD     Load return data
        "60E0"                    + // 56 PUSH1 224
        "1C"                      + // 57 SHR (move deadbeef to least significant)
        `63${retData}`            + // 59 PUSH4 DEADBEEF
        "14"                      + // 64 EQ
        "16"                      + // 65 AND  (successful call and got DEADBEEF)
        `61${storedData}`         + // 66 PUSH2 DAD
        "54"                      + // 69 SLOAD  Should have DAD stored at DAD
        `61${storedData}`         + // 70 PUSH2 DAD
        "14"                      + // 73 EQ
        "16"                      + // 74 AND (also correct storage)
        "604F"                    + // 75 PUSH1 79 (0x4F)
        "57FD"                    + // 77 JUMPI, REVERT
        "5B00"                      // 79 JUMPDEST, STOP
   },


   0xFA: {              // STATICCALL
      test: "0x" +
        str2mem_ml("AABBCCDD", 0xC)  +   // Arguments to send, 4 bytes
        "6000"                    + // 20 PUSH1 0   Not needed, only here
                                    //              to compensate for the
                                    //              fact we don't need to
                                    //              send Value, and I am
                                    //              too lazy to recalcualte
                                    //              addresses
        "6004"                    + // 22 PUSH1 4   Length of return data
        "6000"                    + // 24 PUSH1 0   Memory location for return data
        "6004"                    + // 26 PUSH1 4   Args length
        "6000"                    + // 28 PUSH1 C   Memory location of arguments
        `73${calledContractAddr.slice(2)}` + // 30 PUSH calledContractAddr
        "5A"                      + // 51 GAS       Push the gas amount
        "FA"                      + // 52 STATICCALL      Phew! We finally get to do a call
        "6039"                    + // 53 PUSH1 57 (0x39)
        "5700"                    + // 55 JUMPI, STOP
        "5BFD"                      // 57 JUMPDEST, REVERT
                                    // This call should fail, because the called
                                    // contract writes to storage
   },


   0x3D: {              // RETURNDATASIZE
      test: "0x" +
        str2mem_ml("AABBCCDD", 0xC)  +   // Arguments to send, 4 bytes
        "6004"                    + // 20 PUSH1 4   Length of return data
        "6000"                    + // 22 PUSH1 0   Memory location for return data
        "6004"                    + // 24 PUSH1 4   Args length
        "600C"                    + // 26 PUSH1 C   Memory location of arguments
        "6000"                    + // 28 PUSH1 0   Value, Wei to send
        `73${calledContractAddr.slice(2)}` + // 30 PUSH calledContractAddr
        "5A"                      + // 51 GAS       Push the gas amount
        "F1"                      + // 52 CALL      Phew! We finally get to do a call
        "3D"                      + // 53 RETURNDATASIZE (should be four bytes)
        "6004"                    + // 54 PUSH1 4
        "14"                      + // 56 EQ
        "603D"                    + // 57 PUSH1 61 (0x3D)
        "57FD"                    + // 59 JUMPI, REVERT
        "5B00"                      // 61 JUMPDEST, STOP
   },


   0x3E: {              // RETURNDATACOPY
      test: "0x" +
        str2mem_ml("AABBCCDD", 0xC)  +   // Arguments to send, 4 bytes
        "6004"                    + // 20 PUSH1 4   Length of return data
        "6000"                    + // 22 PUSH1 0   Memory location for return data
        "6004"                    + // 24 PUSH1 4   Args length
        "600C"                    + // 26 PUSH1 C   Memory location of arguments
        "6000"                    + // 28 PUSH1 0   Value, Wei to send
        `73${calledContractAddr.slice(2)}` + // 30 PUSH calledContractAddr
        "5A"                      + // 51 GAS       Push the gas amount
        "F1"                      + // 52 CALL      Phew! We finally get to do a call
        "3D"                      + // 53 RETURNDATASIZE
        "6000"                    + // 54 PUSH1 0 (location in returndata)
        "6000"                    + // 56 PUSH1 0 (location in memory)
        "3E"                      + // 58 RETURNDATACOPY
        "6000"                    + // 59 PUSH1 0   Memory location for return data
        "51"                      + // 61 MLOAD     Load return data
        "60E0"                    + // 62 PUSH1 224
        "1C"                      + // 64 SHR (move deadbeef to least significant)
        `63${retData}`            + // 65 PUSH4 DEADBEEF
        "14"                      + // 70 EQ
        "16"                      + // 71 AND  (successful call and got DEADBEEF)
        "604C"                    + // 72 PUSH1 76 (0x4C)
        "57FD"                    + // 74 JUMPI, REVERT
        "5B00"                      // 76 JUMPDEST, STOP
   },







   0xFD: { // REVERT
     test: "0xFD",
     testRes: 0   // this opcode reverts
   },


   0x39: {   // CODECOPY, read my own code
      test: "0x" +
        "6002"                      + //  0 PUSH1 2   Length of code to copy
        "6002"                      + //  2 PUSH1 2   Offset of the code
        "601E"                      + //  4 PUSH1 30  Offset in memory
                                      //              Use this so the values
                                      //              are written to the least
                                      //              significant value
        "39"                        + //  6 CODECOPY  Copy 2 bytes of code to mem
        "6000"                      + //  7 PUSH1 0
        "51"                        + //  9 MLOAD     Read the memory
        "616002"                    + // 10 PUSH2 6002 What we expect to see
        "14"                        + // 13 EQ        Is this equal?
        "6012"                      + // 14 PUSH1 18 (0x12)
        "57FD"                      + // 16 JUMPI, REVERT
        "5B00"                        // 18 JUMPDEST, STOP
   },


   0x3C: {   // EXTCODECOPY, read another contract's code
      test: "0x" +
        "6004"                      + //  0 PUSH1 4   Length of code to copy
        "6000"                      + //  2 PUSH1 0   Offset of the code
        "601C"                      + //  4 PUSH1 28  Offset in memory
                                      //              Use this so the values
                                      //              are written to the least
                                      //              significant value
        `73${calledContractAddr.slice(2)}` + //  6 PUSH20 calledContractAddr
        "3C"                        + // 27 EXTCODECOPY  Copy 4 bytes of code to mem
        "6000"                      + // 28 PUSH1 0
        "51"                        + // 30 MLOAD     Read the memory
        "6360DE6010"                + // 31 PUSH4     Values we expect to find
        "14"                        + // 36 EQ        Is this equal?
        "6029"                      + // 37 PUSH1 41 (0x29)
        "57FD"                      + // 39 JUMPI, REVERT
        "5B00"                        // 41 JUMPDEST, STOP
   },



   0xFF: {   // SELFDESTRUCT
      test: "0x" +
        "60FF31"                  + //  0 Check contract balance before call
        "6000"                    + //  3 PUSH1 0    Length of return data
        "6000"                    + //  5 PUSH1 0    Memory location for return data
        "6000"                    + //  7 PUSH1 0    Args length
        "6000"                    + //  9 PUSH1 0    Memory location of arguments
        "6000"                    + // 11 PUSH1 0    Value, Wei to send
        "60FF"                    + // 13 PUSH1 FF   Contract address
        "5A"                      + // 15 GAS        Push the gas amount
        "F1"                      + // 16 CALL       Call the suicidal contract
        "50"                      + // 17 POP        Remove the return value
        "60FF31"                  + // 18 Check the contract balance post call
        "14"                      + // 21 EQ         Should not be equal
        "601A"                    + // 22 PUSH1 26 (0x1A)
        "5700"                    + // 24 JUMPI, STOP
        "5BFD"                      // 26 JUMPDEST, REVERT
   },


   0x35: {   // CALLDATALOAD
      test: "0x" +
        "6000"       + //  0 PUSH1 0   Load from the beginning
        "35"         + //  2 CALLDATALOAD
        "61BAD0"     + //  3 PUSH2 BAD0  (the value we expect to get)
        "14"         + //  6 EQ
        "600B"       + //  7 PUSH1 11 (0x0B)
        "57FD"       + //  9 JUMPI, REVERT
        "5B00"         // 11 JUMPDEST, STOP
   },

   0x37: {   // CALLDATACOPY
      test: "0x" +
        "6020"       + //  0 PUSH1 32   Load 32 bytes
        "6000"       + //  2 PUSH1 0    From offset 0 in the call data
        "6010"       + //  4 PUSH1 16   Into offset 0x10 in memory
        "37"         + //  6 CALLDATACOPY
        "6010"       + //  7 PUSH1 16   Read from offset 0x10 in memory
        "51"         + //  9 MLOAD
        "61BAD0"     + // 10 PUSH2 BAD0  (the value we expect to get)
        "14"         + // 13 EQ
        "6012"       + // 14 PUSH1 18 (0x12)
        "57FD"       + // 16 JUMPI, REVERT
        "5B00"         // 18 JUMPDEST, STOP
   }

}  // var opcodes =


// Add the PUSH1 - PUSH32 opcodes
for(var i=0x60; i<0x80; i++)
   opcodes[i] = { test: push_n_ml(i) }


// Add the DUP1 - DUP16 opcodes
for(var i=0x80; i<0x90; i++)
   opcodes[i] = { test: dup_n_ml(i) }


// Add the SWAP1 - SWAP16 opcodes
for(var i=0x90; i<0xA0; i++)
   opcodes[i] = { test: swap_n_ml(i) }


const undefinedOP = op => {
  return {
       test: `0x6001600160016001600160016001${byte2Hex(op)}00`,
       testRes: 0,   // we expect a revert
       fromFork: forks[0]
  }  // return structure
}    // undefinedOP

// Get the full information for an opcode
const getOpcode = op => {
  // The information to test a bad opcode. It should revert. If it doesn't,
  // the test fails. Push values into the stack first so if it is an opcode it
  // won't fail due to stack underflow. After the opcode put a legitimate STOP
  // so it will be a success.

  if (opcodes[op] === undefined)
    return undefinedOP(op)

  // If we get here, the opcode is defined
  return {
    test: opcodes[op].test,

    // If testRes is not defined, assume one. This lets us specify
    // zero for REVERT
    testRes: opcodes[op].testRes == undefined ? 1 : opcodes[op].testRes,

    // If an opcode doesn't have a specified fork, it should work
    // for all forks we test
    fromFork: opcodes[op].fromFork || forks[0]
  }

}  // getOpcode



// Return the contract that tests the opcode
const getOpcodeContract = op => `

    '${opcode2Addr(op)}':
      ${boilerPlate_Contract}
      code: :raw ${getOpcode(op).test}
  `


const getTestContract = (fromOpcode, opcodeNum) => {
  var retVal = `

    '${bigTestContractAddr}':
      ${boilerPlate_Contract}
      code: |
        {
              (mstore8 30 0xBA)
              (mstore8 31 0xD0) `

  for(var i=fromOpcode; i<fromOpcode+opcodeNum; i++)
    retVal += `
              (sstore ${i} (call 10000000 ${opcode2Addr(i)} 0 0 32 0 0))`

  retVal += `
        }`

  return retVal
}


// A contract that can be called and returns data
const getCalledContract = () =>
`

    '${calledContractAddr}':
      ${boilerPlate_Contract}
      code: :raw 0x${str2mem_ml(retData, 0x10)}61${storedData}61${storedData}5560046010F3


`

//  0 Write deadbeef starting at mem location 0x10
// 12 PUSH2 0DAD
// 15 PUSH2 0DAD
// 18 SSTORE
// 19 PUSH1    4    // Length of returned data
// 21 PUSH1 0x10    // Memory location of returned data
// 23 RETURN



// The transaction, which calls the big test contract
const transaction = `
  blocks:
  - transactions:
    - data: :raw 0xFF
      gasPrice: ${gasPrice}
      nonce: auto
      gasLimit: ${gasLimit}
      nonce: 0
      to: ${bigTestContractAddr}
      value: ${transactWei}

    # a94f5374fce5edbc8e2a8697c15331677e6ebf0b
      secretKey: "45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"

`


// Opcode result, true if we expect a STOP, false if we expect a REVERT 
const opcodeRes = (fork, op) => {
  opObj = getOpcode(op)
  forkNum = forks.indexOf(opObj.fromFork)

  if (fork < forkNum)    // We know the fork, and this one is earlier
    return 0
  else
    return opObj.testRes // This is the fromFork, or a later fork.
                         // If the fork in the opcode is unknown,
                         // assume all the ones we care about are after it
}



// The expect section
const getExpect = (fromOpcode, opcodeNum) => {
  var retVal = `

  expect:
`

  for(var i=0; i<forks.length; i++) {
    retVal += `
  - network:
    - ${forks[i]}
    result:
      '${bigTestContractAddr}':
        storage:`

    for (var j=fromOpcode; j<fromOpcode+opcodeNum; j++)
      retVal += `
          '0x${j.toString(16)}': ${opcodeRes(i,j)}`
  }     // for every fork

  return retVal
} // getExpect



const getTest = (fromOpcode, opcodeNum) => {

  console.log(`Test_Opcode_${byte2Hex(fromOpcode)}:`)

  console.log(boilerPlate_Head)

  for(var i=fromOpcode; i<fromOpcode+opcodeNum; i++)
     console.log(getOpcodeContract(i))

  console.log(getTestContract(fromOpcode, opcodeNum))
  console.log(getCalledContract())
  console.log(transaction)
  console.log(getExpect(fromOpcode, opcodeNum))
  console.log('\n\n\n\n')
}


for (var i=0; i<256; i++)
	getTest(i, 1)

