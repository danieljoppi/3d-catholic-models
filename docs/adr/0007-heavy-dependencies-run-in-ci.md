# 0007. Heavy dependencies run in CI

**Status:** Accepted
**Date:** 2026-09-06

## Context

Depth estimation needs torch and transformers — hundreds of megabytes, and a
model checkpoint on top. The rest of the tooling needs the standard library
plus `numpy` and `Pillow`.

Requiring torch to file an image into a folder would be absurd.

## Decision

Everyday tooling — ingest, importers, `new_piece.py`, `inspect_mesh.py`,
`relief_from_heightmap.py` — uses the standard library, `numpy` and `Pillow`,
and nothing else.

Anything heavier runs in GitHub Actions. `.github/workflows/relief.yml`
installs CPU-only torch, estimates depth, meshes the result, and commits the
depth map back.

## Consequences

Anyone can clone and run the tooling. The expensive step needs no local setup
at all — dispatch the workflow and collect the artifact. The whole Station XII
pipeline ran in 56 seconds on a standard runner.

`scripts/depth_map.py` tries a list of model ids in order, so a moved or
renamed checkpoint degrades to the next rather than failing the run.

The cost: producing a depth map requires either CI or a local setup the repo
does not describe in detail, and CI runs are not free.

## Alternatives considered

**One requirements.txt with everything.** Makes every contributor pay torch's
download to run a filing script.

**Ship a container.** More machinery than a two-collection art project needs.
