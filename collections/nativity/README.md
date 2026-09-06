# Nativity

Presépio figures: the Holy Family, the shepherds, the Magi, the animals, the
stable and its furnishings.

Nothing here yet. When the first images arrive, create a set:

```
collections/nativity/<set-name>/
  metadata.json
  README.md
  _inbox/
  pieces/<slug>/{piece.md,reference/,model/{source,export},renders/}
```

A nativity set is naturally one set per scale and style — all its figures
must print at consistent proportions, so keep a set's pieces together and
record the intended figure height in the set's `metadata.json`.

Pieces are added one at a time with `scripts/new_piece.py`, the same as
statues — see [`collections/statues/README.md`](../statues/README.md) for the
workflow, and `docs/folder-structure.md` for the layout.
