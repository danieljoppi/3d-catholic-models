# 0001. Collection / set / item layout

**Status:** Accepted
**Date:** 2026-09-06

## Context

The project began with 15 Stations of the Cross reference images and a stated
intention to add statues and nativity figures later. A flat folder of images
would have needed rearranging the moment the second collection arrived.

Each subject accumulates several kinds of file over its life: the reference
art, an editable working file, one or more print-ready exports, preview
renders, and notes. These belong together.

## Decision

Three levels: **collection** (subject), **set** (one coherent series), **item**
(one station or figure). Every item folder holds `reference/`,
`model/source/`, `model/export/`, `renders/`, and a notes file.

Each set carries a `metadata.json` describing itself and indexing its items.

## Consequences

An item folder is self-contained, so a single station can be zipped and handed
to a parish without untangling it from the rest. A second interpretation of the
same subject is a new set, not a renamed file.

The cost is depth: reaching one image takes five path segments, and an empty
scaffold needs `.gitkeep` files to survive git. Both are acceptable against the
alternative of restructuring later with links and printed labels already out.

## Alternatives considered

**Flat per-collection folders.** Simplest until a subject has more than one
file, which is immediately.

**Separate trees by file type** (`references/`, `models/`, `renders/`).
Groups by the least interesting property. Working on one station would mean
three directories open, and moving a station would touch all of them.
