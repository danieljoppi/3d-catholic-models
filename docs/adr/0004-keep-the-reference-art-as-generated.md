# 0004. Keep the reference art as generated

**Status:** Accepted
**Date:** 2026-09-06

## Context

Set 01's fifteen panels are not stylistically uniform. Panels I–X are shallow
reliefs against a cream limestone arcade in a lighter oak frame with pierced
tracery; XI–XIV are deeper and more crowded, in a darker red-brown wood with a
plainer ogee arch and open landscape; XV returns to the tracery frame inside
the rock tomb.

Since the images were generated, regenerating XI–XIV to match the first ten was
available and was initially suggested as a way to make the set uniform.

## Decision

Keep the references as they are. Achieve uniformity in the models instead:
model the frame once as a reusable component and choose a single relief depth
for all fifteen.

Leave the backgrounds alone.

## Consequences

No regeneration work, and no risk of losing panels that are already good. The
frame becomes a shared component, which is less work than fifteen frames however
the references look.

The backgrounds stay varied — and should. The setting shifts at XI because the
narrative does, leaving the praetorium for Golgotha; carved sets have always let
the scenery follow the story. Normalising it would have removed something
correct.

The cost: a reader comparing the reference images to each other still sees the
discontinuity, so the set README explains it rather than hiding it.

## Alternatives considered

**Regenerate XI–XIV with the arcade and lighter frame.** The original
suggestion. It was based on a wrong premise — that the reference's frame and
relief depth propagate into the model. They do not; both are modelling choices.

**Model each panel exactly as carved.** Faithful to the references, but a Via
Crucis is seen all at once on a wall, and mismatched frames would read as an
accident.
