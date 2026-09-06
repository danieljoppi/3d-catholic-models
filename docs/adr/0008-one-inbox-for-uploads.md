# 0008. One inbox for uploads

**Status:** Accepted
**Date:** 2026-09-06

## Context

Files arrive from outside: reference images, and now meshes generated with
Meshy. Each set had its own `_inbox/`, which meant knowing the set path before
uploading anything — `collections/statues/singles/_inbox/` is not a thing
anyone wants to type or remember.

The asked-for thing was singular: *the* folder to upload to.

## Decision

A top-level `inbox/` with one subfolder per collection, and `inbox/routes.json`
mapping each to its set.

`scripts/ingest.py` drains all of it: images to `reference/`, models to
`model/source/`, matched to items by name, metadata updated, and every STL run
through the print-fault inspector with its report saved alongside.

`.github/workflows/ingest.yml` does the same on any push touching `inbox/`.

## Consequences

Uploading is drag, drop, push. The router needs no inference — the subfolder
says which collection, the filename says which item — so nothing is guessed.

Adding a set means one line in `routes.json`.

The cost is a second path into the collections alongside the per-set
importers, which still exist and are still documented for direct use. They
share their matching logic through `setlib.py`, so the behaviour cannot drift.

## Alternatives considered

**Keep per-set `_inbox/` only.** Correct but unfriendly; it requires knowing
the layout before contributing to it.

**A single flat `inbox/` with the collection inferred from the filename.** One
less folder, and fragile: `sao-jose.jpg` is a plausible statue and a plausible
nativity figure.
