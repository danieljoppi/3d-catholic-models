# Handoff

State of the project as of 2026-09-07, written so another session can pick it
up cold. The 2026-09-06 handoff asked for one thing — a session with network
access to `api.meshy.ai` — and that session has now run; section 3 records what
it found.

---

## 1. Do this first

**Rotate the Meshy API key.** Two live keys have now been pasted in plaintext
into conversations about this repository: one in the conversation that produced
it, one on 2026-09-07. Neither was ever written to a file here
(`tests/check_no_secrets.py` enforces that), but both are in transcripts —
treat both as compromised.

1. Revoke it at meshy.ai and issue a new one.
2. Add the new one as a **repository secret**, not a file:
   Settings → Secrets and variables → Actions → New repository secret,
   named `MESHY_API_KEY`.
3. Never paste it into a chat, a workflow input, or a commit again.

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
docs/  adr/                        10 decision records
scripts/                           tooling
tests/                             fixtures with hand-derived values
```

Start with [`AGENTS.md`](AGENTS.md) for conventions and invariants, then
[`docs/adr/`](docs/adr/) for why anything is the way it is.

## 3. What the Meshy session found

`api.meshy.ai` is reachable now, and the key authenticates. `scripts/meshy.py`
has been corrected against the live API and is no longer written blind. Two
things came out of it — one small, one that changes the plan.

### The endpoints and shapes, verified 2026-09-07

| | |
|---|---|
| `GET /openapi/v1/image-to-3d` | 200, a bare JSON list |
| `GET /openapi/v2/text-to-3d` | 200, a bare JSON list |
| `GET /openapi/v1/balance` | 200, `{"balance": 125}` |
| `GET /openapi/v1/text-to-3d` | 404 `NoMatchingRoute` |
| `GET /openapi/v2/image-to-3d` | 404 `NoMatchingRoute` |

The two guessed endpoints were right, including their mismatched version
numbers. Corrected in the client: `sort_by=-created_at` and a 50-item page cap
with pagination; `created_at` is milliseconds, not seconds; the only
downloadable status is `SUCCEEDED`; a text task is named by its `prompt` and an
image task has no name at all; `model_urls` also offers `3mf`, which matters
here more than `usdz` does; errors arrive as `{"message": ...}`; the invented
`name` / `object_prompt` / `model_url` fallbacks are gone. `tests/test_meshy.py`
pins all of it offline, and `meshy.py balance` is a one-call check that a key
works.

### The part that changes the plan

**The API cannot see the models in the web app.** Every listing returns `[]`
while My Assets holds the fifteen Stations reliefs and a Marian statue. The key
is fine — `balance` answers on it. Meshy keeps API assets and workspace assets
in separate spaces by design, and publishes no endpoint that lists or downloads
workspace assets. Full reasoning in
[ADR-0010](docs/adr/0010-meshy-workspace-is-not-the-api.md).

So no script here will ever pull those reliefs. To get them in:

1. Meshy web app → **My Assets** → the model → download **STL** (or 3MF).
2. Drop the files in `inbox/stations/`, named for the item they belong to —
   `station-12-jesus-dies-on-the-cross.stl` and so on.
3. `scripts/ingest.py --create`, or just push and let `ingest.yml` do it.

`meshy.py` stays useful for anything generated **through the API** later:
those it lists, names from their prompt, and downloads unattended, which is
what `.github/workflows/meshy-fetch.yml` automates. API results expire after
about three days, so that fetch has to be prompt.

### Still blocked

`photos.app.goo.gl` remains unreachable, so the original album still cannot be
downloaded here. The fifteen references were uploaded by hand and are in the
repository; nothing further depends on it.

## 4. Tooling

| Script | Verified? | |
|---|---|---|
| `ingest.py` | yes | Drains `inbox/`, files images and models, inspects meshes |
| `new_piece.py` | yes | Creates a piece before its files exist |
| `import_images.py` | yes | Files images into one set directly |
| `inspect_mesh.py` | yes | STL fault report and repair |
| `relief_from_heightmap.py` | yes | Heightmap → watertight relief panel |
| `depth_map.py` | yes, in CI | Reference → depth map (needs torch) |
| `meshy.py` | yes, against the live API | Lists and downloads **API tasks only** — not the web workspace (ADR-0010) |

Standard library plus `numpy` and `Pillow`. Torch runs only in CI.

### Workflows

| | Trigger | Verified? |
|---|---|---|
| `checks.yml` | push, PR | yes — green on PR #1 |
| `relief.yml` | dispatch | yes — ran Station XII in 56s |
| `ingest.yml` | push to `inbox/` | not yet fired with real files |
| `meshy-fetch.yml` | dispatch | not yet — needs the secret; the client it runs is verified |

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
python3 tests/test_meshy.py       # Meshy response shapes
python3 tests/check_metadata.py   # metadata vs. filesystem
python3 tests/check_no_secrets.py # credential tripwire
```

CI runs all four.
