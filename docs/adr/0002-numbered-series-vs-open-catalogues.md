# 0002. Numbered series vs. open catalogues

**Status:** Accepted
**Date:** 2026-09-06

## Context

The Stations are numbered `01-jesus-is-condemned-to-death` and so on. Applying
the same pattern to statues raised a question: what number does a saint get?

A station's number is part of its identity. Station IV is Station IV in every
set ever carved, it appears on the panel in gilt, and the order is liturgical.
A statue's number would be whatever order the figures happened to arrive in.
Adding one figure later would either break the ordering or force renumbering
everything after it — and item ids appear in printed labels.

## Decision

A set declares itself with `"numbered": true|false`.

**Numbered series** fix their items in `metadata.json` up front, use
`<NN>-<slug>` folders, and match incoming files by number.

**Open catalogues** accumulate pieces one at a time, use `<slug>` folders with
no number, and match incoming files by slug.

The tooling reads the flag and behaves accordingly; nothing else differs.

## Consequences

Statues and nativity figures can be added indefinitely without disturbing what
exists. Stations keep the numbering that is genuinely theirs.

The cost is two code paths in every importer, and a reader must check the flag
before assuming a folder name's shape. The shared matching helpers in
`setlib.py` keep that to one branch in one place.

## Alternatives considered

**Number everything.** Uniform, and wrong: it invents an ordering statues do
not have, then makes that invention expensive to change.

**Number nothing.** Loses real information. `04-jesus-meets-his-mother` sorts
and reads correctly; `jesus-meets-his-mother` alone does not tell you where in
the Via Crucis it falls.
