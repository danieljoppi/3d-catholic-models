# 0006. What belongs in git

**Status:** Accepted
**Date:** 2026-09-06

## Context

This project generates large binaries. A single relief STL at working
resolution is 21 MB; fifteen would be over 300 MB, regenerated every time a
parameter changes. GitHub warns above 50 MB per file and rejects above 100 MB.

Some generated files are not really disposable, though. A depth map is
generated once and then corrected by hand — dodging and burning it is the
actual modelling work — so it is an input, not an output.

## Decision

Version anything that is **edited by hand or expensive to reproduce**:
reference images, depth maps, shaded previews, notes, metadata.

Keep out anything **mechanically reproducible from those**: STL and 3MF
exports, slicer output. Meshes built in CI are uploaded as workflow artifacts
instead.

`.gitattributes` marks binary formats as binary and carries commented Git LFS
patterns for when a real hand-made source file (a `.blend`) needs versioning.

## Consequences

The repository stays clonable. The full state of the work is still captured —
every committed input plus the scripts reproduces every output.

The cost: a finished export is not permanently addressable in git. Workflow
artifacts expire after 30 days, so a genuinely final print-ready mesh will
eventually want a release attachment or LFS. That decision can wait until
there is one.

## Alternatives considered

**Version the STLs.** Straightforward and quickly makes the repository
unpleasant to clone, for files that are a script run away.

**Git LFS for everything now.** Real cost and setup friction before there is
anything that needs it. The patterns are written and commented out, ready.
