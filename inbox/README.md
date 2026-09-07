# inbox — drop uploads here

**This is the only folder you need to upload to.** Put files in the
subfolder for their collection and everything else is automatic.

```
inbox/
  stations/    Stations of the Cross  ->  collections/stations-of-the-cross/set-01
  statues/     Statues                ->  collections/statues/singles
  nativity/    Nativity               ->  collections/nativity/set-01
```

`routes.json` maps each subfolder to its set; edit it when you add a set.

## Naming

Name each file after the item it belongs to. That is the whole trick.

| Collection | Name it | Example |
|---|---|---|
| Stations | by number | `07.jpg`, `station-07.stl`, `estacao-07.glb` |
| Statues, nativity | by piece slug | `sacred-heart-of-jesus.stl`, `sao-jose.jpg` |

Accents are fine in the name — `são-josé.stl` resolves to `sao-jose`.

## Models made in the Meshy web app

Download them from **My Assets** as STL (or 3MF) and drop them here, named for
their item. There is no script for this: models generated in the web app live
in a space the Meshy API cannot read, so `scripts/meshy.py` will not find them
however full My Assets looks — see
[ADR-0010](../docs/adr/0010-meshy-workspace-is-not-the-api.md). `meshy.py`
fetches models generated through the API, which is a different set of files.

## Then run

```sh
scripts/ingest.py                # everything waiting in inbox/
scripts/ingest.py --dry-run      # show the plan, change nothing
scripts/ingest.py statues        # one collection only
```

Or push to the branch and let `.github/workflows/ingest.yml` do it — it runs
on any push that touches `inbox/`, files everything, inspects the meshes, and
commits the result.

## What happens to each kind of file

| Kind | Goes to | Then |
|---|---|---|
| Images (`.jpg .png .webp .tif .heic`) | `<item>/reference/` | Written into the item's notes file |
| Models (`.stl .obj .glb .gltf .ply .3mf .fbx .blend`) | `<item>/model/source/` | Inspected for print faults; report saved beside it |

Ingested files are **moved**, not copied, so an empty inbox means everything
landed. Nothing is overwritten without `--force`.

## Pieces that do not exist yet

For statues and nativity, a file naming a piece that does not exist is refused
rather than guessed at. Either create it first:

```sh
scripts/new_piece.py collections/statues/singles "Sacred Heart of Jesus"
```

or let the ingest create it from the filename:

```sh
scripts/ingest.py --create
```

## Size

GitHub warns above 50 MB per file and rejects above 100 MB. If a model is
larger, either enable Git LFS (patterns are commented in `.gitattributes`) or
decimate it before uploading — `scripts/inspect_mesh.py` reports the triangle
count so you know what you are dealing with.
