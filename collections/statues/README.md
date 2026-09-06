# Statues

Standalone devotional figures — saints, the Sacred Heart, Our Lady under her
various titles, crucifixes.

## Sets

| Set | |
|---|---|
| [`singles/`](singles/) | Figures with no series of their own. The default home for a statue. |

A themed series — one artist, one commission, the four evangelists, a parish's
set of patrons — gets its own `set-NN/` alongside `singles/`, structured
identically.

## Adding a figure

Statues are an open catalogue rather than a fixed series, so a piece is created
when its idea is, before any image exists:

```sh
scripts/new_piece.py collections/statues/singles "Sacred Heart of Jesus" \
    --pt "Sagrado Coração de Jesus" \
    --la "Sacratissimum Cor Iesu" \
    --feast "Friday after Corpus Christi" \
    --attributes "flaming heart, crown of thorns, cross above the heart"
```

That builds the folder tree, writes `piece.md`, and registers the piece in
`metadata.json`. Accents are handled — *São José Operário* becomes
`sao-jose-operario`.

## Adding its image

Drop the image in `singles/_inbox/`, named after the piece, and import:

```sh
scripts/import_images.py collections/statues/singles --dry-run
scripts/import_images.py collections/statues/singles --move
```

Unlike the Stations, matching is by **name, not number** — `sacred-heart-of-jesus.jpg`
finds its piece. A file matching nothing is refused rather than guessed at; pass
`--create` to have it create the piece from the filename instead.

Importing fills the image into `piece.md` and ticks its first checkbox.

## Why no numbers

Station folders are numbered because the number *is* the station's identity —
Station IV is Station IV in every set ever carved. A statue's number would be
arbitrary, and adding one figure later would either break the ordering or force
renumbering the rest. So pieces are named for their subject alone:

```
pieces/sacred-heart-of-jesus/
pieces/our-lady-of-fatima/
pieces/sao-jose-operario/
```

## Iconography comes first

`piece.md` opens with an **Iconography** section — attributes, vesture, posture
— before any modelling note. Keys for Peter, the lily for Joseph, the flaming
heart crowned with thorns. A statue that prints beautifully but hands a saint
the wrong attribute is not that saint, and that is the one mistake a devotional
model cannot survive.

See `docs/folder-structure.md` and `docs/naming-conventions.md`.
