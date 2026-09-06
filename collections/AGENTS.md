# collections/

Content, not code. Each collection holds sets; each set holds items; each item
folder is self-contained so a single station or figure can be zipped and handed
to a parish on its own.

## Two kinds of set

| | Numbered series | Open catalogue |
|---|---|---|
| Example | Stations of the Cross | Statues, nativity |
| `"numbered"` | `true` | `false` |
| Items | Fixed in metadata up front | Accumulate one at a time |
| Folder | `04-jesus-meets-his-mother` | `sacred-heart-of-jesus` |
| Images match by | Number in the filename | Piece slug |

The reasoning is in ADR-0002: a station's number *is* its identity, a statue's
would be arbitrary.

## Editing metadata.json

Prefer the tooling — `new_piece.py`, `ingest.py` — which keeps the file and the
filesystem in step. Hand edits are fine, but run `tests/check_metadata.py`
afterwards.

Never renumber a numbered set and never rename an item id. Both appear in
printed labels and links.

## Per-collection notes

- **stations-of-the-cross** — 14 traditional stations plus the Resurrection.
  Set 01's panels are not stylistically uniform; that is a property of the
  reference art, not a constraint on the models (ADR-0004).
- **statues** — `singles/` is the default home for a standalone figure. A
  themed series gets its own set.
- **nativity** — one set is one scale and one style. Set
  `scale.figure_height_mm` before modelling; the figures must stand together.
