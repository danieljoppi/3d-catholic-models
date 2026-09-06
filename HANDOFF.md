# Handoff

State of the project as of 2026-09-06, written so another session — one with
network access to `api.meshy.ai` — can pick it up cold.

---

## 1. Do this first

**Rotate the Meshy API key.** A live key was pasted in plaintext into the
conversation that produced this repository. It is in that transcript. It was
never written to any file here (`tests/check_no_secrets.py` enforces that), but
treat it as compromised.

1. Revoke it at meshy.ai and issue a new one.
2. Add the new one as a **repository secret**, not a file:
   Settings → Secrets and variables → Actions → New repository secret,
   named `MESHY_API_KEY`.
3. Never paste it into a chat, a workflow input, or a commit again.

**Set `main` as the default branch.** Settings → Branches. The repository was
empty when this work started, so the feature branch became the default and I
could not change it through the API.

---

## 2. What exists

A working project: three organized collections, all 15 Stations references
filed and described, an upload pipeline, a relief-modelling pipeline proven end
to end, mesh repair tooling, tests, and decision records.

```
inbox/<collection>/        the only upload folder; ingest drains it
collections/
  stations-of-the-cross/set-01/    15 panels, complete, described
  statues/singles/                 ready, no pieces yet
  nativity/set-01/                 ready, no pieces yet
docs/  adr/                        9 decision records
scripts/                           tooling
tests/                             fixtures with hand-derived values
```

Start with [`AGENTS.md`](AGENTS.md) for conventions and invariants, then
[`docs/adr/`](docs/adr/) for why anything is the way it is.

## 3. The blocker this handoff exists to solve

This session's egress policy blocked two hosts outright:

| Host | Consequence |
|---|---|
| `photos.app.goo.gl` | Could not download the original album; the owner uploaded the 15 images by hand instead |
| `api.meshy.ai` | **Could not call Meshy at all** |

So `scripts/meshy.py` and `.github/workflows/meshy-fetch.yml` are **written but
never executed against the real API**. Everything else in the repository has
been run and verified.

### What is unverified, specifically

`scripts/meshy.py` guesses at Meshy's response shape. These are the assumptions
to check first:

```python
BASE = "https://api.meshy.ai"
ENDPOINTS = [("image-to-3d", "/openapi/v1/image-to-3d"),
             ("text-to-3d",  "/openapi/v2/text-to-3d")]
# auth:     Authorization: Bearer <key>
# listing:  a bare list, or {"result": [...]}, or {"data": [...]}
# per task: id, status ("SUCCEEDED"), name/prompt, model_urls {stl, glb, obj, fbx, usdz}
```

**Correct them from a real response, not from memory.** The client has a probe
mode for exactly this:

```sh
export MESHY_API_KEY=...        # the rotated one
scripts/meshy.py probe          # dumps raw JSON of one page
```

Then fix `ENDPOINTS`, `model_urls()` and `describe()` to match, and run:

```sh
scripts/meshy.py list
scripts/meshy.py fetch-all --collection statues --format stl --dry-run
scripts/meshy.py fetch-all --collection statues --format stl
scripts/ingest.py --create
```

Or, once the secret is set, do the whole thing in CI without a local key —
Actions → **Fetch from Meshy** → mode `probe`, then `fetch`.

## 4. Tooling

| Script | Verified? | |
|---|---|---|
| `ingest.py` | yes | Drains `inbox/`, files images and models, inspects meshes |
| `new_piece.py` | yes | Creates a piece before its files exist |
| `import_images.py` | yes | Files images into one set directly |
| `inspect_mesh.py` | yes | STL fault report and repair |
| `relief_from_heightmap.py` | yes | Heightmap → watertight relief panel |
| `depth_map.py` | yes, in CI | Reference → depth map (needs torch) |
| `meshy.py` | **no** | Written blind; see section 3 |

Standard library plus `numpy` and `Pillow`. Torch runs only in CI.

### Workflows

| | Trigger | Verified? |
|---|---|---|
| `checks.yml` | push, PR | yes — green on PR #1 |
| `relief.yml` | dispatch | yes — ran Station XII in 56s |
| `ingest.yml` | push to `inbox/` | not yet fired with real files |
| `meshy-fetch.yml` | dispatch | **no** — needs the secret |

## 5. Where the modelling actually got to

Station XII went through the full pipeline: **431,730 triangles, 287 cm³,
watertight with outward normals**, from a depth estimate rather than luminance.
The depth map and a shaded preview are committed; the STL was a workflow
artifact and has since expired.

The estimate read the panel correctly — frame nearest, sky farthest, Christ
proud at the centre with the mourners in front. Four things it cannot do, all
recorded in that station's notes:

- Faces come out featureless. They must be sculpted.
- Pierced Gothic tracery turns to soft ripples — model the frame as real
  geometry once and reuse it across all fifteen.
- A raised lip along the bottom border, where the estimate runs out.
- The whole relief is slightly melted next to the carving.

The other fourteen stations have **not** been run. `relief.yml` takes a station
and dimensions as inputs, so they are one dispatch each.

## 6. Open decisions, for the owner

- **Licence for derived models.** `rights.licence` is `TBD` in every set. The
  references are the owner's own Gemini-generated work, so no third party is
  involved, but the models need a licence before distribution. CC BY-SA or
  CC BY-NC are the usual choices for devotional work meant to reach parishes.
- **Print size and material cost.** Station XII at 150 mm is 287 cm³ — roughly
  350 g of filament, so about 5 kg for all fifteen. Hollowing the back or
  dropping to 100 mm cuts that sharply. Worth settling before a production run.
- **Nativity scale.** `scale.figure_height_mm` is `null`. Nativity figures must
  agree with each other; set it before modelling anything.

## 7. Conventions worth not rediscovering

- Item ids are permanent — they appear in printed labels and links.
- Accents live in titles, never on disk: *São José Operário* → `sao-jose-operario`.
- Numbered series (stations) vs. open catalogues (statues, nativity) —
  [ADR-0002](docs/adr/0002-numbered-series-vs-open-catalogues.md).
- Generated meshes are **not** committed; they are rebuilt —
  [ADR-0006](docs/adr/0006-what-belongs-in-git.md).
- Geometry claims need fixtures with hand-derived values, never captured
  output — [ADR-0009](docs/adr/0009-hand-derived-test-fixtures.md). This caught
  two real bugs that were invisible in the output: side walls wound inward
  (watertight, correctly sized, *negative* volume) and `--height-mm` measuring
  a shell it had already dropped (12 mm when 180 mm was asked for).

## 8. Before committing anything

```sh
tests/test_mesh_tools.sh          # 17 fixtures
python3 tests/check_metadata.py   # metadata vs. filesystem
python3 tests/check_no_secrets.py # credential tripwire
```

CI runs all three.
