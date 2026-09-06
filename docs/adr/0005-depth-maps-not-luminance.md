# 0005. Depth maps, not luminance, for reliefs

**Status:** Accepted
**Date:** 2026-09-06

## Context

A bas-relief is a compressed depth map, so a reference image can drive one
directly. The cheap way is to treat brightness as height: feed the photo in,
displace a plane by its grayscale.

On these panels it fails predictably. Christ's crimson robe is dark and in
front; the cream limestone arcade is bright and behind. Luminance would sink
the central figure into the wall behind it.

## Decision

`scripts/relief_from_heightmap.py` takes a **heightmap** and does not attempt
to derive one. Depth comes from a monocular depth estimator
(`scripts/depth_map.py`), which predicts distance per pixel.

A `--luminance` flag builds from a photo anyway, prints a warning saying the
result is preview-only, and exists so the failure can be seen rather than
described.

## Consequences

The mesher stays a deterministic geometry tool, testable against fixtures with
known volumes, and independent of whichever depth model is current. Any
heightmap works: estimated, hand-painted, or corrected.

Proven on Station XII: the estimate read the panel correctly — frame nearest,
sky farthest — and the composition survived, with Christ proud at the centre
and the mourners in front of him.

The cost is a second step and a heavy dependency for it (ADR-0007), and the
estimate still needs hand correction: faces come out featureless, pierced
Gothic tracery turns to soft ripples, and the estimate leaves a raised lip at
the image border.

## Alternatives considered

**Luminance displacement.** Wrong for the reason above, and the failure is not
subtle.

**Depth estimation inside the mesher.** Couples a deterministic, testable tool
to a large model dependency and to whichever checkpoint is fashionable.
