# 0011. Link to community models, never vendor them

**Status:** Accepted
**Date:** 2026-09-07

## Context

The mission is a furnished chapel, not a demonstration that we can model
everything ourselves. Someone in the middle of nowhere with a printer needs an
altar, candlesticks, a crucifix, a font and a Via Crucis — and does not care
which of those we sculpted.

A survey of MakerWorld and Printables on 2026-09-07 found the community has
already solved a good part of it, unevenly:

| Mission area | What the community has |
|---|---|
| Sacred statuary | Plenty. Marian figures, Padre Pio, St Joseph, Holy Family, saint sets |
| Crucifixes | Plenty, from classical scans to modern reinterpretations |
| Holy water fonts | A few, including a dedicated Catholic Object Library account |
| Candle holders | Many, but decorative — cathedral-*inspired*, not liturgical furniture |
| The Liturgical Heart | Thin. Altar frontals, ambons and tabernacle adornments are mostly dollhouse miniatures, not furniture to be printed at size |
| Stations of the Cross | No complete set found |

So the gap is not "Catholic models"; it is *liturgical* models at real scale,
and a coherent Via Crucis. That is where original work earns its keep, and it
is a much smaller job than modelling a whole chapel from nothing.

The obvious move — collect the good third-party STLs into this repository — is
not available. Every model carries its own licence, chosen per upload, and the
range includes terms that forbid exactly that: MakerWorld's Standard Digital
File License permits personal printing only, with no file redistribution and no
remixes, and Creative Commons ND variants forbid distributing modified
versions. A licence also belongs to a *model*, not a platform, so there is no
blanket answer to reason from.

Nor can we check any of it automatically. Both makerworld.com and
printables.com return **403** to programmatic requests, so no script here can
read a licence, confirm a model still exists, or notice that its terms changed.

## Decision

**We link to community models. We never copy their files into this repository.**

1. `docs/sourcing-models.md` holds the curated catalogue: where to look per
   mission area, and specific starting points. Links and notes only.
2. **The licence is read on the model's own page, by a person, at the moment
   they download it** — never assumed from the platform, from a sibling model
   by the same designer, or from what this catalogue said on some earlier date.
3. Third-party files live in the user's slicer, not in `collections/`. What is
   in `collections/` is ours to license, which is what makes ADR-0003 —
   provenance recorded before distribution — enforceable at all.
4. **We model what the survey says is missing**, and check the catalogue before
   starting anything new. A pretty crucifix that already exists twenty times
   over is not a contribution.

## Consequences

The project can furnish a chapel long before it can sculpt one, and the
catalogue is honest about which pieces are ours.

It costs:

- **The catalogue rots and nothing here notices.** Links die, models are
  withdrawn, licences are changed by their authors. With both platforms
  refusing automated requests there is no link-checker to write; it is a
  periodic human read-through or nothing.
- **We cannot promise a user anything about a linked model.** Not that it is
  still free, not that it prints, not that it is any good. The catalogue says
  where to look and what we thought of it, and stops there.
- **No single download.** A chapel comes from this repository plus several
  other sites, each with its own account and terms. A one-click bundle would be
  a licence violation, not a feature.
- **The mission statement overpromises for a while.** "Everything you need"
  currently means "a curated route to most of it, and a Via Crucis we are
  making ourselves."

## Alternatives considered

**Vendor the STLs into `collections/`.** The obvious version of the idea, and
licence-fatal: several of the best models are under terms that forbid
redistribution outright, and per-model diligence at that scale is a job nobody
will keep doing. One mistake is a takedown, and it would poison a repository
whose whole provenance story (ADR-0003) is that every file in it is accounted
for.

**Git submodules or a download manifest that pulls files at build time.** Same
copying, one layer of indirection away, and it breaks the moment a platform
requires a login — which both of these already do for automated access.

**Model everything ourselves.** Purest, and it never ships. One station took a
full pipeline and still needs hands on the faces; a chapel is hundreds of
pieces. Deliberately duplicating good work that is already free also fails the
"beauty and reverence" test — a worse crucifix is not a contribution because we
made it.

**Curate silently — just links in the README.** Rejected for what it leaves
out. The licence rule is the load-bearing part, and it needs somewhere to be
written down where a contributor will trip over it.
