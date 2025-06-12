"""
The Prague fork enables deploying code into externally owned accounts (EOAs)
via the [`SetCodeTransaction`], increases the blob throughput, increases the
cost of calldata-heavy transactions, introduces general execution layer
requests (and two request types: [consolidation][c], and [withdrawal][w]),
appends validator deposits to execution layer blocks, creates BLS12-381
precompiles, and exposes historical block hashes through [a system
contract][b].

[`SetCodeTransaction`]: ref:ethereum.prague.transactions.SetCodeTransaction
[c]: ref:ethereum.prague.requests.CONSOLIDATION_REQUEST_TYPE
[w]: ref:ethereum.prague.requests.WITHDRAWAL_REQUEST_TYPE
[b]: ref:ethereum.prague.fork.HISTORY_STORAGE_ADDRESS
"""

from ethereum.fork_criteria import ByTimestamp

FORK_CRITERIA = ByTimestamp(1746612311)
