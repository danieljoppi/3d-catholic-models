# Naming conventions

Lowercase, ASCII, hyphen-separated. No spaces, no accents, no `#`, and no
Roman numerals in filenames — accents and Roman numerals belong in the
human-facing title fields, not on disk.

## Item folders

Numbered series carry the number; open catalogues do not.

```
<NN>-<slug>          numbered series (Stations of the Cross)
01-jesus-is-condemned-to-death
15-the-resurrection

<slug>               open catalogue (statues, nativity)
sacred-heart-of-jesus
our-lady-of-fatima
sao-jose-operario
```

`NN` is zero-padded so the folders sort correctly. The slug describes the
subject in English; localised titles live in the item's notes file and in
`metadata.json` (`pt-BR` and `la` today). Accents are stripped in slugs and
kept in titles — *São José Operário* is `sao-jose-operario` on disk.

`scripts/new_piece.py` derives the slug for you.

## Reference images

```
reference/<item>.<ext>                 the primary artwork
reference/<item>--detail-<nn>.<ext>    crops, close-ups, alternates
```

`scripts/import_images.py` produces the primary name automatically.

## Model files

```
model/source/<collection>_<set>_<item>_v<NN>.blend
model/export/<collection>_<set>_<item>_<size>_v<NN>.stl
```

where `<item>` is the item folder's name, numbered or not:

Example:

```
stations-of-the-cross_set-01_12-jesus-dies-on-the-cross_v03.blend
stations-of-the-cross_set-01_12-jesus-dies-on-the-cross_150mm_v03.stl
statues_singles_sacred-heart-of-jesus_v01.blend
statues_singles_sacred-heart-of-jesus_200mm_v01.stl
```

`<size>` is the longest edge of the intended print in millimetres. Version
numbers only ever go up; a superseded export is deleted, not kept as
`_old` or `_final2`.

## Renders

```
renders/<item>--<view>.png             view: front, angle, detail, lit
```
