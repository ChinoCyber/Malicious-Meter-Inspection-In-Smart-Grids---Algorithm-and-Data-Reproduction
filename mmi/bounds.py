"""Information-theoretic floor for the MMI problem.

Every probe answers one yes/no question ("is this subtree clean?").
When the m dirty meters are placed uniformly at random there are
C(n, m) equally likely arrangements, so ANY correct adaptive strategy
needs on average at least log2 C(n, m) probes.  A measured (or
published) curve below this line under uniform placement is impossible.
The bound does not apply to clustered/spread placements, whose
arrangement distributions carry less entropy.
"""

import math

_LOG2 = math.log(2)


def information_lower_bound(n, m):
    """log2 C(n, m) via lgamma (exact enough for plotting)."""
    if m <= 0 or m >= n:
        return 0.0
    return (math.lgamma(n + 1) - math.lgamma(m + 1)
            - math.lgamma(n - m + 1)) / _LOG2
