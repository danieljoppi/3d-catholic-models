# 0009. Hand-derived test fixtures

**Status:** Accepted
**Date:** 2026-09-06

## Context

The geometry tools make claims that are easy to get wrong and hard to eyeball.
A mesh can be watertight and inside out. A repair can look plausible and change
the volume. An STL viewer will happily display a broken mesh.

Two real bugs proved the point. The relief mesher wrote side walls with
inverted winding — the mesh was watertight, correctly sized, and enclosed
negative volume. And `--height-mm` measured its bounding box before pruning
vertices, so scaling a mesh after `--drop-shells` used the extent of the shell
it had just discarded, producing a 12 mm model when 180 mm was asked for.

Neither was visible in the output. Both were caught by arithmetic.

## Decision

Every geometry claim has a fixture whose expected value is **derived by hand**,
never captured from the code's own output.

A 10 mm cube encloses 1000 mm³ because that is what 10³ is. A cube with one
wall removed has exactly 4 boundary edges. An inside-out cube reports −1.00 cm³.
Four of twelve faces wound backwards give 0.33 cm³, and repair returns 1.00.

`tests/test_mesh_tools.sh` holds these; CI runs it on every push.

## Consequences

A regression in winding, welding, hole filling, or scaling fails loudly instead
of shipping a mesh that looks fine and prints wrong. The fixtures are also
documentation: reading them tells you what the tools promise.

The cost is that fixtures must be worked out by hand, which is slower than
recording current behaviour — and that is the whole point, since recording
current behaviour would have locked in both bugs above.

## Alternatives considered

**Golden-file tests.** Cheap to write and would have enshrined the inverted
normals as correct.

**Trust the slicer.** Slicers auto-repair silently, so they hide exactly the
faults worth knowing about.
