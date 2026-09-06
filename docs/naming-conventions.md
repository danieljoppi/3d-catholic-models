# Naming conventions

Lowercase, ASCII, hyphen-separated. No spaces, no accents, no `#`, and no
Roman numerals in filenames — accents and Roman numerals belong in the
human-facing title fields, not on disk.

## Item folders

```
<NN>-<slug>
01-jesus-is-condemned-to-death
15-the-resurrection
```

`NN` is zero-padded so the folders sort correctly. The slug describes the
subject in English; localised titles live in `station.md` and `metadata.json`
(`pt-BR` and `la` today).

## Reference images

```
reference/<NN>-<slug>.<ext>                 the primary artwork
reference/<NN>-<slug>--detail-<nn>.<ext>    crops, close-ups, alternates
```

`scripts/import_stations.py` produces the primary name automatically.

## Model files

```
model/source/<collection>_<set>_<NN>-<slug>_v<NN>.blend
model/export/<collection>_<set>_<NN>-<slug>_<size>_v<NN>.stl
```

Example:

```
stations-of-the-cross_set-01_12-jesus-dies-on-the-cross_v03.blend
stations-of-the-cross_set-01_12-jesus-dies-on-the-cross_150mm_v03.stl
```

`<size>` is the longest edge of the intended print in millimetres. Version
numbers only ever go up; a superseded export is deleted, not kept as
`_old` or `_final2`.

## Renders

```
renders/<NN>-<slug>--<view>.png        view: front, angle, detail, lit
```
