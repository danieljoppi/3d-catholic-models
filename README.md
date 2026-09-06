# 3D Catholic Models

Ideas and working files for Catholic 3D models — beautiful images for
personal devotion, and pieces small parishes can print themselves.

## What is here

| Path | |
|---|---|
| [`collections/stations-of-the-cross/set-01/`](collections/stations-of-the-cross/set-01/) | First Via Crucis series — 14 stations plus the Resurrection |
| [`collections/statues/`](collections/statues/) | Standalone figures — awaiting the first set |
| [`collections/nativity/`](collections/nativity/) | Presépio figures — awaiting the first set |
| [`docs/`](docs/) | Folder structure, naming conventions, printing guide |
| [`scripts/`](scripts/) | Import tooling |

## Status of Set 01

The 15 reference images are **not yet in the repository**. The album host
(`photos.app.goo.gl`) is blocked by the network policy of the environment
this structure was built in, so the folders, metadata, and import script are
ready and waiting for the files.

To import them:

```sh
# download the album, unzip into the set's _inbox/, then:
scripts/import_stations.py collections/stations-of-the-cross/set-01 --dry-run
scripts/import_stations.py collections/stations-of-the-cross/set-01 --move
```

Details in [the set's README](collections/stations-of-the-cross/set-01/README.md).

## How a piece progresses

```
reference image  ->  model/source/  ->  model/export/  ->  test print  ->  renders/
```

Each item's `station.md` (or `piece.md`) carries that checklist, the
scripture reference, and the print notes learned from the first proof.

## Adding a new collection

Same shape every time — a collection, a set inside it, one folder per item:

```
collections/<collection>/<set>/pieces/<NN-slug>/
```

`docs/folder-structure.md` has the full layout and the reasoning behind it.

## Large files

Reference photos and meshes are binary and grow fast. If the repository gets
heavy, move `*.stl`, `*.3mf`, `*.blend`, and the reference images to
[Git LFS](https://git-lfs.com) — the layout here does not change, only how
those files are stored.

## Rights

Devotional artwork is not automatically public domain. Every set's
`metadata.json` has a `rights` block; fill in the artist and the licence
before publishing or distributing a model derived from someone else's image.
