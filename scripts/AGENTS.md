# scripts/

Standard library only, plus `numpy` and `Pillow` for the mesh and image tools.
Anything heavier runs in CI (ADR-0007).

| Script | |
|---|---|
| `setlib.py` | Shared: set loading, slugs, matching, item trees, notes. Not a CLI. |
| `ingest.py` | Drains `inbox/` — the entry point people actually use |
| `import_images.py` | Files images into one set directly |
| `new_piece.py` | Creates a piece before its files exist |
| `inspect_mesh.py` | STL print-fault report and repair |
| `relief_from_heightmap.py` | Heightmap to watertight relief panel |
| `depth_map.py` | Reference image to depth map (needs torch; CI only) |

## Rules

- **Shared logic goes in `setlib.py`.** Matching, slugs, and note-writing were
  duplicated across importers once already; do not do it again.
- **Refuse rather than guess.** An unmatched upload gets an error naming the
  fix. Filing it somewhere plausible is worse than stopping.
- **Every CLI takes `--dry-run`** where it writes anything.
- **Geometry needs a test.** Expected values are derived by hand — a 10 mm cube
  encloses 1000 mm³ because of arithmetic, not because the script agrees with
  itself. Add fixtures to `tests/test_mesh_tools.sh`.
- **Exit quietly on `BrokenPipeError`** — these get piped into `head`.
- **Never clobber hand-written prose.** `setlib.write_notes` creates a notes
  file if absent and otherwise only refreshes two known lines.
