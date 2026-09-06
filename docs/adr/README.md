# Architecture decision records

Why things are the way they are. Each record states the decision, what forced
it, and what it costs — so a later reader can tell a considered choice from an
accident, and knows what to weigh when reversing one.

| # | Decision | Status |
|---|---|---|
| [0001](0001-collection-set-item-layout.md) | Collection / set / item layout | Accepted |
| [0002](0002-numbered-series-vs-open-catalogues.md) | Numbered series vs. open catalogues | Accepted |
| [0003](0003-provenance-before-distribution.md) | Provenance recorded before distribution | Accepted |
| [0004](0004-keep-the-reference-art-as-generated.md) | Keep the reference art as generated | Accepted |
| [0005](0005-depth-maps-not-luminance.md) | Depth maps, not luminance, for reliefs | Accepted |
| [0006](0006-what-belongs-in-git.md) | What belongs in git | Accepted |
| [0007](0007-heavy-dependencies-run-in-ci.md) | Heavy dependencies run in CI | Accepted |
| [0008](0008-one-inbox-for-uploads.md) | One inbox for uploads | Accepted |
| [0009](0009-hand-derived-test-fixtures.md) | Hand-derived test fixtures | Accepted |

New record: copy [`template.md`](template.md), take the next number, add a row.
A superseded record stays in place with its status changed and a pointer to
what replaced it — the history is the point.
