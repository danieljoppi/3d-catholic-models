# Printing guide

Notes that apply across the collections. Per-item findings go in that item's
`station.md` or `piece.md` under **Print notes**.

## Two audiences, two sizes

| Audience | Typical size (longest edge) | Notes |
|---|---|---|
| Personal devotion | 80–150 mm | Fits a home altar or a bedside shelf; a full set of 15 stays affordable in filament. |
| Small church | 250–400 mm | Usually printed in sections and joined; plan the seams into the model. |

Model once at real proportions and scale at slicing time. Detail that
survives at 300 mm disappears at 80 mm, so check the small size before
calling a station finished.

## Relief vs. free-standing

Stations work best as **bas-relief** panels: one flat back, no supports, fast
prints, and they hang on a wall the way a Via Crucis is meant to. Aim for a
relief depth of 8–15% of the panel's height.

Statues and nativity figures are free-standing and need support planning,
usually a print orientation tilted to keep supports off the face.

## Mesh checks before export

- Manifold, no holes, no self-intersections.
- Wall thickness ≥ 1.2 mm anywhere the print must survive handling.
- No feature thinner than the nozzle (0.4 mm) — fingers, rays, and thin
  crosses are where this bites.
- Decimate to a workable triangle count; slicers choke long before the
  detail becomes visible.

## Export

`.3mf` when the slicer supports it — it carries units and orientation.
`.stl` as the universal fallback. Put both in `model/export/` if useful.

## Rights

Devotional art is not automatically public domain. Record the artist and the
licence of every source image in the set's `metadata.json` before publishing
or sharing a derived model.
