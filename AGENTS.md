# Working in this repository

**Chapel Anywhere** — open-source, 3D-printable sacred art, enough of it to
furnish a chapel's interior from scratch: altar ornamentation, statues of the
saints, a Via Crucis. Read this before changing anything.

## The shape of it

```
inbox/<collection>/     the only upload folder; scripts/ingest.py drains it
collections/<collection>/<set>/
    metadata.json       the set's index — the tooling's source of truth
    <item_dir>/<item>/  reference/ model/{source,export}/ renders/ + notes
docs/                   conventions, pipelines, ADRs
scripts/                tooling
tests/                  fixtures with hand-derived expected values
```

## Invariants

Break these and the tooling breaks with them.

1. **`metadata.json` and the filesystem agree.** Every item has a folder;
   every folder is an item. `tests/check_metadata.py` enforces it.
2. **Item ids are permanent.** They appear in printed labels, file names, and
   links. Add and deprecate; do not rename.
3. **A set is numbered or it is not**, declared by `"numbered"`. Numbered sets
   have fixed items and numbered folders; open catalogues accumulate pieces
   with slug-only folders. See ADR-0002.
4. **Provenance is recorded before distribution.** Every set has a `rights`
   block. A reference from someone else's carving carries their rights; a
   generated one does not. See ADR-0003.
5. **Generated binaries stay out of git** — meshes are rebuilt from their
   inputs. Depth maps and previews are committed because they are edited by
   hand and small. See ADR-0006.

## Conventions

- Lowercase ASCII slugs, hyphen separated. Accents live in titles, never on
  disk: *São José Operário* is `sao-jose-operario`. `setlib.slugify` does it.
- Titles carry `en`, `pt-BR` and `la`. English is required; the others may be
  `null` until someone fills them in.
- Item notes (`station.md`, `piece.md`) are written by tooling and edited by
  hand afterwards. Tooling must never clobber hand-written sections — see
  `setlib.write_notes`, which creates but only ever refreshes two known lines.

## Before you commit

```sh
tests/test_mesh_tools.sh     # mesh tooling against hand-derived fixtures
python3 tests/test_meshy.py  # Meshy response shapes
python3 tests/check_metadata.py
python3 -m compileall -q scripts
```

CI runs all of these on push (`.github/workflows/checks.yml`), plus the
credential tripwire `tests/check_no_secrets.py`.

## Adding tooling

- Shared logic goes in `scripts/setlib.py`. Two scripts doing nearly the same
  thing is the smell this repo has already had once.
- Standard library only, except `numpy` and `Pillow` for the mesh and image
  tools. Anything heavier (torch) runs in CI, never in everyday tooling —
  ADR-0007.
- Every geometry claim needs a test with an expected value derived by hand,
  not captured from the code's own output. A cube is 1000 mm³ because it is a
  10 mm cube, not because the script said so. Two real bugs were caught this
  way: inverted side-wall winding, and `--height-mm` measuring a shell it had
  already dropped.
- Fail loudly rather than guessing. An unmatched upload is refused with a
  message naming the fix, not filed somewhere plausible.

## Domain notes

Iconography is not decoration. Keys for Peter, the lily for Joseph, the flaming
heart crowned with thorns. A model that prints beautifully but hands a saint
the wrong attribute is not that saint — `piece.md` therefore leads with
iconography, ahead of any modelling note.

Nativity figures must agree on scale with each other; statues need not. That is
why nativity sets carry `scale.figure_height_mm`.
