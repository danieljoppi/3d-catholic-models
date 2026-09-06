# Nativity

Presépio figures: the Holy Family, the shepherds, the Magi, the animals, the
stable and its furnishings.

## Sets

| Set | |
|---|---|
| [`set-01/`](set-01/) | First presépio — structure ready, no pieces yet |

One set is one scale and one style. A second presépio — a different size for a
different room, a different carving style — is a new set, never mixed into an
existing one.

## Why scale matters more here

Statues stand alone; nativity figures stand together. The set's
`metadata.json` carries `scale.figure_height_mm`, the height of a standing
adult figure, and every other piece is proportioned from it. Fix it before
modelling, not after the first print.

Pieces are added one at a time with `scripts/new_piece.py`, the same as
statues — see [`collections/statues/README.md`](../statues/README.md) for the
workflow, and `docs/folder-structure.md` for the layout.
