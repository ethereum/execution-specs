"""
The Bogota fork is the development fork after Amsterdam. It carries no
protocol changes yet: EIPs targeting it are prototyped on their own
``eips/bogota/*`` branches and land here once accepted.

### Changes

None yet.

### Releases

"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
