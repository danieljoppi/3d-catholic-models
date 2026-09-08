# Chapel Anywhere

An open-source initiative providing everything you need to build a chapel's
interior from scratch. From full altar ornamentation to detailed statues of
saints, we offer high-quality 3D-printable sacred art so anyone can build a
complete place of worship, anywhere in the world.

## About

The 3D printing community offers endless models for pop culture and tabletop
games, but finding beautiful, high-quality Catholic sacred art is a real
challenge. **Chapel Anywhere** was created to fill this void.

Imagine you are in the middle of nowhere, working with a tight budget, but you
want to build a chapel from scratch. You have the walls and the roof, but you
need everything else inside. With a 3D printer and this repository, you can
bring that chapel to life.

Our mission is to provide every element needed to furnish and adorn a complete
prayer space — a growing, open-source library of STLs, focused on beauty and
reverence:

- **The Liturgical Heart** — designs for the sanctuary: altar frontals, ambons
  (lecterns), and tabernacle adornments.
- **Sacred Statuary** — highly detailed statues of Our Lady, St Joseph,
  St Padre Pio, and other saints to grace the sides of your altar.
- **Wall and space elements** — a complete 14-piece Stations of the Cross,
  crucifixes, and holy water fonts.
- **Smart assembly** — modular designs that print on smaller beds, and ornate
  pieces that attach to standard wooden structures to build larger altars.

### Two ways we get there

We do not have to sculpt all of it. Much of what furnishes a chapel has already
been modelled well by the community and given away, so the project runs on two
supply lines:

- **Curated** — [`docs/sourcing-models.md`](docs/sourcing-models.md) is a route
  through what already exists on MakerWorld and Printables: crucifixes, Marian
  and saint statues, holy water fonts, candle holders. Links only. We never
  copy anyone's files in here, because their licences are set per model and
  several forbid it outright — read the licence on the model's own page, every
  time ([ADR-0011](docs/adr/0011-link-to-community-models-never-vendor-them.md)).
- **Ours** — the pieces nobody has published. A survey on 2026-09-07 found the
  community thorough on devotional figures, patchy on the sanctuary, and empty
  on **a complete Stations of the Cross**. That last one is what we make, and
  it is why set 01 exists.

### Where that stands today

Honestly: early. The repository holds three collections — a Via Crucis series
with all fifteen references filed and described, plus statues and a presépio
scaffolded but empty — the reference art behind them, and a pipeline that turns
a reference image into a watertight, print-checked mesh. One station has been
through it end to end. The curated route will furnish a chapel long before our
own catalogue can; that is the point of having both.

## What is here

| Path | |
|---|---|
| [`collections/stations-of-the-cross/set-01/`](collections/stations-of-the-cross/set-01/) | First Via Crucis series — 15 carved relief panels, all imported |
| [`collections/statues/`](collections/statues/) | Standalone figures — structure ready, no pieces yet |
| [`collections/nativity/`](collections/nativity/) | Presépio figures — structure ready, no pieces yet |
| [`inbox/`](inbox/) | **Upload here** — drop files, push, the pipeline files them |
| [`docs/`](docs/) | [Sourcing models](docs/sourcing-models.md), [making the models](docs/making-the-models.md), folder structure, naming, printing, [ADRs](docs/adr/) |
| [`tests/`](tests/) | Fixtures with hand-derived expected values |
| [`scripts/`](scripts/) | Import and scaffolding tooling |

## Status of Set 01

All reference images are imported: **the 14 traditional stations**, plus the
Resurrection as a companion panel — 15 in all, filed by the gilt Roman numeral
carved into each. They are carved polychromed wood reliefs in Gothic tracery
frames, 896×1200 JPEG.

The Via Crucis is fourteen stations, and the set is described as fourteen. The
Resurrection ships with it but is marked a companion rather than a fifteenth
station ([ADR-0012](docs/adr/0012-the-resurrection-is-a-companion-not-a-station.md)).

Every station folder has its image, its composition notes, and its checklist.
Station XII has an automated first pass — depth map and a shaded preview are
committed, and [its notes](collections/stations-of-the-cross/set-01/stations/12-jesus-dies-on-the-cross/station.md)
record what the depth estimate got right and the four things it cannot do. The
other fourteen have not been run, and nothing is sculpted by hand yet.

The panels are not stylistically uniform — I–X are shallow reliefs on a cream
limestone arcade, XI–XIV are deeper and darker with a plainer arch — but the
frame and the relief depth are modelling choices, not inherited from the
reference. See the
[set README](collections/stations-of-the-cross/set-01/README.md#style).

## How a piece progresses

```
reference image  ->  model/source/  ->  model/export/  ->  test print  ->  renders/
```

Each item's `station.md` (or `piece.md`) carries that checklist, the
scripture reference, and the print notes learned from the first proof.

## Two kinds of set

The Stations are a **numbered series**: fifteen fixed items where the number is
the identity, declared in `metadata.json` up front, images matched by number.

Statues are an **open catalogue**: pieces accumulate one at a time, folders are
named for the subject with no number, and images are matched by name.

```
collections/stations-of-the-cross/set-01/stations/04-jesus-meets-his-mother/
collections/statues/singles/pieces/sacred-heart-of-jesus/
```

Both use the same folder tree inside an item and the same tooling — a set says
which it is with `"numbered": true|false`. `docs/folder-structure.md` has the
full layout and the reasoning.

## Tooling

| | |
|---|---|
| `scripts/ingest.py` | **Drain `inbox/`** — files images and models, inspects meshes |
| `scripts/meshy.py` | Pull models generated **through the Meshy API** into `inbox/`. Web-app models are a separate space it cannot read — export those by hand ([ADR-0010](docs/adr/0010-meshy-workspace-is-not-the-api.md)) |
| `scripts/new_piece.py <set> "<name>"` | Create a piece — folder tree, notes, metadata entry |
| `scripts/import_images.py <set>` | File images from `_inbox/` into their items |
| `scripts/relief_from_heightmap.py <img>` | Turn a depth map into a watertight relief panel STL |
| `scripts/inspect_mesh.py <stl>` | Check an STL for print faults; `--fix` repairs them |

The first two take `--dry-run`; `import_images.py` takes `--move` to empty the
inbox and `--create` to add pieces it does not recognise. The mesher and the
inspector need `numpy` and `Pillow`.

## Automation

| Workflow | Runs on | |
|---|---|---|
| `checks.yml` | push, PR | Mesh fixtures, Meshy response shapes, metadata, credential tripwire |
| `ingest.yml` | push touching `inbox/` | Files uploads, inspects meshes, commits the result |
| `relief.yml` | manual dispatch | Depth map and relief mesh for one station; needs torch, which is why it runs here |
| `meshy-fetch.yml` | manual dispatch | Pulls Meshy **API** tasks into `inbox/`; needs the `MESHY_API_KEY` repository secret |

## Uploading

One folder: [`inbox/`](inbox/). Drop files in the subfolder for their
collection, named after the item they belong to, and either run
`scripts/ingest.py` or just push — `.github/workflows/ingest.yml` does it.

```
inbox/stations/07.jpg                      -> station 07's reference/
inbox/statues/sacred-heart-of-jesus.stl    -> that piece's model/source/
```

Meshes are inspected for print faults on the way in and their report saved
beside them. Details in [`inbox/README.md`](inbox/README.md).

## Making the models

Check [`docs/sourcing-models.md`](docs/sourcing-models.md) first — if the
community already has it, print theirs.

For the gaps: the Stations are relief panels and the statues are figures in the
round; those are different problems and the relief one is much more tractable.
See [`docs/making-the-models.md`](docs/making-the-models.md) for both pipelines
and the suggested first move.

## Large files

Reference photos and meshes are binary and grow fast. If the repository gets
heavy, move `*.stl`, `*.3mf`, `*.blend`, and the reference images to
[Git LFS](https://git-lfs.com) — the layout here does not change, only how
those files are stored.

## Contributing

[`AGENTS.md`](AGENTS.md) has the conventions and invariants. Before committing:

```sh
tests/test_mesh_tools.sh
python3 tests/check_metadata.py
```

Decisions and their reasoning live in [`docs/adr/`](docs/adr/).

## Licence

Two licences, because this repository holds two different kinds of thing.

| What | Licence | |
|---|---|---|
| Models, reference art, documentation | [**CC BY-SA 4.0**](LICENSE) | Print them, adapt them, sell what you print — attribute, and license derivatives under the same terms |
| Code — `scripts/`, `tests/` | [**MIT**](LICENSE-CODE) | Do essentially anything |

ShareAlike is deliberate. A parish paying a local print shop is a commercial
transaction, and a non-commercial licence would have blocked precisely the
person this project exists for. What it does ask in return is that
improvements to the models come back out under the same terms.

Attribute like this:

> Chapel Anywhere by Daniel Joppi — CC BY-SA 4.0

**One honest caveat.** The Stations reference panels were generated with Google
Gemini Pro, and purely AI-generated images are generally not copyrightable in
the US and several other jurisdictions. For those image files the licence grant
may well be moot — they are arguably free to everyone already. The 3D models
sculpted from them are original human work, and are protected and licensed
normally. No third-party artist's rights are involved either way.

Every set's `metadata.json` carries a `rights` block. A set that ever comes
from someone else's artwork needs the artist and licence recorded there before
anything derived from it is shared —
[ADR-0003](docs/adr/0003-provenance-before-distribution.md).

**Third-party models linked from
[`docs/sourcing-models.md`](docs/sourcing-models.md) are not covered by any of
this.** They carry their own licences, set by their own authors, and none of
their files are in this repository — read each licence on its own page
([ADR-0011](docs/adr/0011-link-to-community-models-never-vendor-them.md)).
