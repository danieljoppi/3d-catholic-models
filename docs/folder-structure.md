# Folder structure

```
collections/
  <collection>/            stations-of-the-cross, statues, nativity, ...
    <set>/                 one coherent series or one artist's set
      metadata.json        machine-readable index of the set
      README.md            what the set is, where it came from
      _inbox/              raw downloads land here before import
      stations/ | pieces/  one folder per item
        <NN-slug>/         numbered series; <slug>/ for an open catalogue
          station.md       or piece.md — notes, scripture/iconography, status
          reference/       source artwork the model is based on
          model/
            source/        editable files (.blend, .zpr, .3mf project)
            export/        print-ready meshes (.stl, .3mf)
          renders/         preview images of the model
docs/                      conventions and guides
scripts/                   helper tooling
```

## Why one folder per item

Everything about a single station — its reference, its working file, its
exports, its notes — stays together. A station folder can be zipped and shared
with a parish on its own, and adding a second interpretation of the same
subject means adding a new set, not renaming files.

## Collections

| Collection | Contains | Item folder |
|---|---|---|
| `stations-of-the-cross` | Via Crucis series, 14 or 15 items | `stations/` |
| `statues` | Standalone figures — saints, Sacred Heart, Our Lady | `pieces/` |
| `nativity` | Presépio figures, grouped per set | `pieces/` |

## Numbered series vs. open catalogues

A set is **numbered** when the number is part of each item's identity — the
Stations of the Cross, where Station IV is Station IV in every set ever carved.
Its items are fixed in `metadata.json` up front and their folders are
`<NN>-<slug>`.

A set is an **open catalogue** when items accumulate — statues, and most
nativity work. Numbers there would be arbitrary and adding one figure would
force renumbering the rest, so folders are `<slug>` alone and pieces are added
one at a time with `scripts/new_piece.py`.

`metadata.json` declares which it is with `"numbered": true|false`, and the
tooling follows suit: numbered sets match images by number, open catalogues
match by name.

New collections follow the same shape: a `<set>/` with `metadata.json`, an
`_inbox/`, and one folder per item.

## Sets

A set is one coherent series: a single artist, a single style, a single
commission. `set-01` is the first Stations series. Sets are numbered, never
renamed, so links and printed labels stay valid.
