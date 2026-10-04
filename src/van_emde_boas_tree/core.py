"""Van Emde Boas tree over bounded integer keys.

Design choice: universe size must be an exact power of two, enforced in the
constructor. Bitwise operations replace division and modulo throughout the
hot path, which is idiomatic for vEB trees and avoids per-call floor/div.

The recursion bottoms out at u == 2, where the structure degenerates to a
plain bitset of two cells. This is the standard base case and keeps the
recursion finite without special-casing u == 1 (which holds no keys).

find_prev / find_next on an empty tree return None rather than raising. This
matches how the predecessor/successor operators behave in the CLRS exposition
("nil" sentinel), translated to Python idiom.
"""

from __future__ import annotations

from typing import Optional


class VEBTree:
    """An ordered set of non-negative integer keys below a fixed power-of-two
    bound.

    All operations run in O(log log u) time where u is the universe size.
    Keys are integers in [0, u). Inserting, deleting, or querying a key at or
    above u raises ValueError.
    """

    __slots__ = ("u", "_mask", "_lo", "_min", "_max", "_summary", "_cluster")

    def __init__(self, u: int) -> None:
        if u < 2 or (u & (u - 1)) != 0:
            raise ValueError("universe size must be a power of two >= 2")
        self.u = u
        # _mask splits a key into (high, low): high = key >> shift, low = key & _mask.
        # Computed once at construction; cheaper than deriving halves per call.
        self._mask = (u >> 1) - 1
        self._lo = u >> 1
        self._min: Optional[int] = None
        self._max: Optional[int] = None
        if u > 2:
            self._summary: Optional[VEBTree] = VEBTree(self._lo)
            self._cluster: Optional[list] = [None] * self._lo
        else:
            # Base case: no children. min/max alone encode the two possible keys.
            self._summary = None
            self._cluster = None

    # ---- internal helpers -------------------------------------------------

    def _high(self, x: int) -> int:
        return x >> (self._lo.bit_length() - 1)

    def _low(self, x: int) -> int:
        return x & self._mask

    def _index(self, high: int, low: int) -> int:
        return (high << (self._lo.bit_length() - 1)) | low

    # ---- public API -------------------------------------------------------

    def __contains__(self, x: object) -> bool:
        if not isinstance(x, int) or isinstance(x, bool):
            return False
        if x < 0 or x >= self.u:
            return False
        if self._min is None:
            return False
        if self._min == x or self._max == x:
            return True
        if self.u == 2:
            return False
        assert self._cluster is not None
        c = self._cluster[self._high(x)]
        return c is not None and self._low(x) in c

    def __len__(self) -> int:
        if self._min is None:
            return 0
        if self.u == 2:
            return 2 if self._min != self._max else 1
        assert self._cluster is not None
        total = 1  # the min element is stored implicitly
        for c in self._cluster:
            if c is not None:
                total += len(c)
        return total

    def insert(self, x: int) -> None:
        """Insert x into the set. Idempotent if x is already present."""
        if not isinstance(x, int) or isinstance(x, bool):
            raise TypeError("key must be an int")
        if x < 0 or x >= self.u:
            raise ValueError(f"key {x} out of universe [0, {self.u})")
        if self._min is None:
            self._min = self._max = x
            return
        if x == self._min or x == self._max:
            return
        if x < self._min:
            x, self._min = self._min, x  # old min moves into a cluster
        if self.u > 2:
            assert self._summary is not None and self._cluster is not None
            high = self._high(x)
            low = self._low(x)
            cluster = self._cluster[high]
            if cluster is None:
                cluster = VEBTree(self._lo)
                self._cluster[high] = cluster
            if cluster._min is None:
                self._summary.insert(high)
                cluster._min = cluster._max = low
            else:
                cluster.insert(low)
        if x > self._max:
            self._max = x

    def delete(self, x: int) -> None:
        """Remove x from the set. No-op if x is absent."""
        if not isinstance(x, int) or isinstance(x, bool):
            raise TypeError("key must be an int")
        if x < 0 or x >= self.u:
            raise ValueError(f"key {x} out of universe [0, {self.u})")
        if self._min is None or x < self._min or x > self._max:
            return
        if x != self._min and x != self._max and x not in self:
            return
        if self._min == self._max:
            if self._min == x:
                self._min = self._max = None
            return
        if self.u == 2:
            # Exactly one of {0,1} remains. The survivor becomes both min and max.
            survivor = 1 - x
            self._min = self._max = survivor
            return
        assert self._summary is not None and self._cluster is not None
        if x == self._min:
            first_cluster = self._summary.find_next(0)
            assert first_cluster is not None
            x = self._index(first_cluster, self._cluster[first_cluster]._min)
            self._min = x
        high = self._high(x)
        low = self._low(x)
        cluster = self._cluster[high]
        assert cluster is not None
        cluster.delete(low)
        if cluster._min is None:
            self._summary.delete(high)
            self._cluster[high] = None
            if x == self._max:
                smax = self._summary.find_prev(self._lo - 1)
                self._max = self._min if smax is None else self._index(smax, self._cluster[smax]._max)
        elif x == self._max:
            self._max = self._index(high, cluster._max)

    def find_next(self, x: int) -> Optional[int]:
        """Return the smallest key >= x, or None if none exists."""
        if not isinstance(x, int) or isinstance(x, bool):
            raise TypeError("key must be an int")
        if x < 0:
            x = 0
        if x >= self.u:
            return None
        if self._min is None:
            return None
        if x <= self._min:
            return self._min
        if x > self._max:
            return None
        if self.u == 2:
            return x  # x in (min, max], base case holds both keys
        assert self._summary is not None and self._cluster is not None
        high = self._high(x)
        low = self._low(x)
        cluster = self._cluster[high]
        if cluster is not None and cluster._max is not None and low <= cluster._max:
            return self._index(high, cluster.find_next(low))
        successor_cluster = self._summary.find_next(high + 1)
        if successor_cluster is None:
            return None
        succ = self._cluster[successor_cluster]
        assert succ is not None and succ._min is not None
        return self._index(successor_cluster, succ._min)

    def find_prev(self, x: int) -> Optional[int]:
        """Return the largest key <= x, or None if none exists."""
        if not isinstance(x, int) or isinstance(x, bool):
            raise TypeError("key must be an int")
        if x >= self.u:
            x = self.u - 1
        if x < 0:
            return None
        if self._min is None:
            return None
        if x >= self._max:
            return self._max
        if x < self._min:
            return None
        if self.u == 2:
            return x
        assert self._summary is not None and self._cluster is not None
        high = self._high(x)
        low = self._low(x)
        cluster = self._cluster[high]
        if cluster is not None and cluster._min is not None and low >= cluster._min:
            return self._index(high, cluster.find_prev(low))
        predecessor_cluster = self._summary.find_prev(high - 1)
        if predecessor_cluster is None:
            return self._min
        pred = self._cluster[predecessor_cluster]
        assert pred is not None and pred._max is not None
        return self._index(predecessor_cluster, pred._max)

    def __iter__(self):
        if self._min is None:
            return
        x = self._min
        while x is not None:
            yield x
            x = self.find_next(x + 1) if x < self.u - 1 else None
