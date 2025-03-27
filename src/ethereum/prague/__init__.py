"""
The Prague fork.
"""

from ethereum.fork_criteria import ByTimestamp

# TODO: Note that this is a dummy timestamp since the
# timestamp for Prague is not finalised at the time of creating this PR.
# The timestamp will have to be updated once Prague goes live.
FORK_CRITERIA = ByTimestamp(1710338138)
