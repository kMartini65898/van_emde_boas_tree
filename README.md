A Van Emde Boas tree: an ordered set of non-negative integer keys bounded by a fixed power of two, with predecessor/successor/insert/delete all in O(log log u).

```python
from van_emde_boas_tree import VEBTree

t = VEBTree(1 << 16)
t.insert(42)
t.insert(1000)
print(42 in t)            # True
print(t.find_next(50))    # 1000
print(t.find_prev(1000))  # 1000
t.delete(42)
print(len(t))             # 1
```

Exported names: `VEBTree` (the only public class).

Why this library exists
-----------------------
When you need a dynamic ordered set over a known, bounded integer domain and
predecessor/successor queries dominate, a balanced BST gives O(log n) per
operation while a vEB tree gives O(log log u). For u in the range of a machine
word (say 2^32) that is roughly five probes per operation regardless of n. The
trade-off is memory: the structure fans out recursively, so the constant
factor is large compared to a hash set, and the universe size must be fixed at
construction time.

Universe size must be an exact power of two (2, 4, 8, ...); the constructor
raises ValueError otherwise. Keys are integers in [0, u). Inserting or
deleting out of that range raises ValueError; non-int keys raise TypeError.

The awkward edge
----------------
`bool` is a subclass of `int` in Python. This library deliberately rejects
booleans as keys (TypeError on insert, `False` for membership) so a caller who
passes `True` by accident does not silently corrupt the set with key `1`. If
you genuinely need 0/1 as keys, pass them as plain ints.

`find_next` and `find_prev` clamp out-of-range arguments into [0, u) before
searching, so `find_next(u)` returns the same as `find_next(u-1)` and
`find_prev(-1)` returns the same as `find_prev(0)`. This matches the vEB
"nil-or-result" convention rather than raising on a query just past the end.
