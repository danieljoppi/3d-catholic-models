# 3D Catholic Models

Ideas and working files for Catholic 3D models — beautiful images for
personal devotion, and pieces small parishes can print themselves.

## What is here

| Path | |
|---|---|
| [`collections/stations-of-the-cross/set-01/`](collections/stations-of-the-cross/set-01/) | First Via Crucis series — 15 carved relief panels, all imported |
| [`collections/statues/`](collections/statues/) | Standalone figures — awaiting the first set |
| [`collections/nativity/`](collections/nativity/) | Presépio figures — awaiting the first set |
| [`docs/`](docs/) | Folder structure, naming conventions, printing guide |
| [`scripts/`](scripts/) | Import tooling |

## Status of Set 01

All 15 reference images are imported — the 14 traditional stations plus the
Resurrection, filed by the gilt Roman numeral carved into each panel. They are
carved polychromed wood reliefs in Gothic tracery frames, 896×1200 JPEG.

Every station folder has its image, its composition notes, and its checklist.
No models sculpted yet — that is the next step.

One thing to settle first: the set is not stylistically uniform. Panels I–X are
shallow reliefs on a cream limestone arcade; XI–XIV are deeper, more crowded,
in a darker wood with a plainer arch. The
[set README](collections/stations-of-the-cross/set-01/README.md#style) has the
detail and the decision it implies.

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
