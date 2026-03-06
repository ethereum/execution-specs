"""
abstract: DELEGATECALL chain benchmark cases (TODO — needs spamoor deploy).

   This file is a placeholder for DELEGATECALL chain benchmarks that
   require heavy pre-deployed state via spamoor. See the design notes
   at the end of this file for the planned test architecture.
"""

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


# ═══════════════════════════════════════════════════════════════════════
# TODO: DELEGATECALL Chain + Cold Code Loading + SSTORE Benchmarks
# ═══════════════════════════════════════════════════════════════════════
#
# STATUS: Not implemented. Requires 50-100 small "library" contracts
# pre-deployed and spread across the trie for realistic cold-access
# patterns. These should be deployed via spamoor and the test run
# with `--execute remote`.
#
# ─── CONCEPT ──────────────────────────────────────────────────────────
#
# DELEGATECALL preserves the caller's storage context while loading
# code from a cold contract. A chain A→B→C→D→E means 4 cold code
# loads (2,600 gas each) but all SSTOREs write to A's storage. This
# is the real-world pattern used by diamond proxies and modular
# contract architectures (e.g., EIP-2535 Diamonds).
#
#   [Caller EOA]
#       │
#       └──► [Entry Contract A] (via EIP-7702 delegation)
#               │ DELEGATECALL ──► [Library B] (cold code load)
#               │                     │ DELEGATECALL ──► [Library C]
#               │                     │                     │ ...
#               │                     │                     └── SSTORE
#               │                     │                         (writes
#               │                     │                          to A's
#               │                     │                          storage)
#               └── All storage mutations land on A
#
# ─── DEPLOYMENT REQUIREMENTS ─────────────────────────────────────────
#
# 1. Deploy 50-100 small "library" contracts via spamoor
#    - Each library is ~50 bytes: DELEGATECALL forward + SLOAD/SSTORE
#    - Libraries should be spread across the trie (different address
#      prefixes) to ensure cold account access on each DELEGATECALL
#    - Use CREATE2 with varied salts for deterministic, spread addresses
#
# 2. Deploy an "entry" contract that knows the library addresses
#    - Takes a chain depth parameter and the library address list
#    - Initiates the DELEGATECALL chain
#
# 3. Alternatively, use EIP-7702 delegation on an EOA:
#    - Authority EOA delegates to a "chain executor" contract
#    - Chain executor DELEGATECALLs through the library contracts
#    - SSTOREs land on the authority's storage
#
# ─── PLANNED VARIANTS ────────────────────────────────────────────────
#
# | Variant                    | Depth | Gas/chain | Stress target     |
# |----------------------------|-------|-----------|-------------------|
# | Pure cold chain            | 3,5,8 | ~8K–21K  | Cold code loading |
# | Chain + SSTORE at leaf     | 5     | ~35K     | Cold + storage    |
# | Chain + SLOAD at each hop  | 5     | ~24K     | Storage reads     |
# |                            |       |           | through delegation|
#
# Gas breakdown per hop (cold DELEGATECALL):
#   - GAS_COLD_ACCOUNT_ACCESS: 2,600 (includes DELEGATECALL base)
#   - Code loading overhead:   varies by library size
#
# At depth 5 (all cold):
#   - 5 * 2,600 = 13,000 gas for cold access
#   - Plus SSTORE at leaf: 22,100 (cold SET = 2,100 + 20,000)
#     or 5,000 (cold RESET = 2,100 + 2,900)
#
# ─── WHY THIS NEEDS SPAMOOR ─────────────────────────────────────────
#
# For realistic cold-access patterns, the library contracts must be:
#   1. Deployed at addresses spread across the trie (not sequential)
#   2. Present in the actual chain state (not just test pre-state)
#   3. Numerous enough (50-100) that a single block's DELEGATECALL
#      chains encounter many cold accounts
#
# With `--execute remote`, the libraries persist across test runs and
# the trie structure reflects real-world deployment patterns.
#
# ─── IMPLEMENTATION NOTES ────────────────────────────────────────────
#
# Library bytecode template (minimal DELEGATECALL forwarder):
#   - Read next-hop address from calldata
#   - DELEGATECALL(gas=GAS, next_hop, 0, CALLDATASIZE, 0, 0)
#   - Or at leaf: SSTORE(CALLDATALOAD(0), CALLDATALOAD(32))
#
# The entry contract / EIP-7702 executor:
#   - Receives: [chain_depth, library_addrs[], slot, value]
#   - Loops: for i in 0..chain_depth, DELEGATECALL to library[i]
#   - Each library forwards to the next, final one does SSTORE
#
# Key metric: ratio of cold code loading gas to useful work (SSTORE).
# At depth 5 with cold SET: ~13,000 gas for cold access vs ~22,100
# for SSTORE = 37% overhead just from the delegation chain.
# ═══════════════════════════════════════════════════════════════════════
