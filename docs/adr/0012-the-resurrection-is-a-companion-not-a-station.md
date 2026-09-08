# 0012. The Resurrection is a companion, not a station

**Status:** Accepted
**Date:** 2026-09-08

## Context

Set 01 was built with fifteen panels: the fourteen traditional Stations of the
Cross, and the Resurrection. The project's public description promises a
"complete 14-piece Stations of the Cross". Both cannot be right.

The Via Crucis is fourteen stations. That number is fixed by long devotional
practice, and a parish printing a Via Crucis expects fourteen — it is what the
walls of a church are laid out for. The Resurrection is a genuine and common
addition in modern practice, sometimes called the fifteenth station, but it is
an addition. Presenting fifteen as *the* Stations of the Cross misdescribes
what the set is.

The obvious fix — delete the Resurrection, or renumber it out of the way — runs
into an invariant. Item ids are permanent (AGENTS.md, invariant 2): they appear
in printed labels, file names, and links, and the rule is add and deprecate,
never rename. `15-the-resurrection` is already filed, described, and referenced.

There is also a mechanical constraint. `setlib.match_numbered` pairs uploaded
files to items by the number in the filename, so `15.jpg` finds the Resurrection
by its `number` field. Setting that number to null to express "not a station"
would break ingest for that panel.

## Decision

**The Resurrection stays in the set, keeps its id and its number, and is marked
as a companion rather than a station.**

1. Its metadata item carries `"companion": true` and a note saying why.
2. The set carries `"traditional_count": 14` alongside `"item_count": 15`. The
   first is what the set *is*; the second is how many folders are on disk.
3. `tests/check_metadata.py` enforces that `traditional_count` equals the
   number of items not marked companion, so the flag cannot silently rot.
4. Everything user-facing says fourteen stations, with the Resurrection named
   separately as a companion panel.
5. **`number: 15` is a permanent id, not a station number.** It is retained
   because ingest matches files by it.

## Consequences

The public description is now true, and a parish gets the fourteen it expects
without the Resurrection being thrown away.

It costs:

- **`number` no longer means only "position in the sequence".** For companions
  it is just a stable handle. That is a genuine wart: the same field carries two
  meanings, and the comment in `check_metadata.py` is doing the work of keeping
  it straight.
- **`15-the-resurrection` reads like a fifteenth station** and always will,
  because the id is permanent. Anyone reading the folder listing will need the
  metadata or this record to know otherwise.
- **A second companion would need thought.** With numbering still required to
  be 1..N across all items, a companion can only ever sit at the end of the
  range. A set wanting companions in the middle would need the numbering rule
  reworked.

## Alternatives considered

**Renumber the Resurrection to null and loosen the numbering check.** The
cleanest expression of the idea, and it breaks `match_numbered`, which uses
`number` as a dictionary key. Fixing that means changing ingest to handle
numberless items in a numbered set — real work, for a field that is only ever
read by one function.

**Move it to its own set or collection.** Honest, and it strands a panel that
belongs with the others: it was generated in the same run, in the same style,
in the same frame. It would also break the permanent-id rule, since the path is
part of how the item is referenced.

**Delete it.** Loses a good reference panel to satisfy a count, and the
Resurrection is a legitimate part of many modern Via Crucis devotions. The
project has no reason to be stricter than the devotion.

**Change the public description to say fifteen.** Considered and rejected by
the owner. Fourteen is what people search for and what a church is laid out
for; leading with fifteen would misdescribe the set to exactly the audience the
project is aimed at.
