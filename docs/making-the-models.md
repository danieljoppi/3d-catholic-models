# Making the models

The collections pose two different problems, and conflating them wastes the
most time.

| | Stations of the Cross | Statues and nativity |
|---|---|---|
| Form | Bas-relief panel, one flat back | Figure in the round |
| What is needed | A depth map, displaced | A full 3D body, including a back nobody photographed |
| Difficulty | Tractable, largely automatable | Genuinely hard; the reference shows one side |

A relief *is* a compressed depth map, so a reference image gets you most of the
way. A statue is not — the reference shows one view, and the other 300° have to
be invented. Start with the Stations.

---

## Path A — relief panels (the Stations)

```
reference image
   -> depth map            (a model estimates distance, per pixel)
   -> hand correction      (fix what the estimate got wrong)
   -> displaced mesh       (scripts/relief_from_heightmap.py)
   -> frame + backing      (modelled once, reused for all 15)
   -> slice and print
```

### 1. Depth map, not luminance

The tempting shortcut is to feed the photo in as a heightmap: bright = high.
It fails predictably. Christ's crimson robe is dark and in front; the cream
limestone arcade is bright and behind. Luminance would sink the figure into the
wall.

What you want is a **monocular depth estimate** — a model that predicts
distance per pixel. Open options that run locally include Depth Anything and
Marigold; plenty of hosted tools do the same. Output a 16-bit grayscale PNG,
near = white. Tooling in this space moves fast, so check what is current rather
than trusting this list.

### 2. Correct it by hand

Depth estimators are trained on photographs, and these are photographs *of a
carving* — so the estimate often reads the carved scene as if it were a real
one, and gets the shallow, compressed depth of a relief wrong. Expect to fix:

- Figures that should sit proud of the background but do not.
- The frame, which should be flat and even, coming out lumpy.
- Faces and hands flattening into the mass behind them.

Painting corrections over the depth map in any image editor — dodge to raise,
burn to lower — is faster than fixing the mesh afterwards and is how a careful
relief actually gets finished.

### Running the whole thing in CI

Depth estimation needs torch, which is too heavy to keep in the everyday repo
tooling, so `.github/workflows/relief.yml` runs the pipeline on a GitHub
runner instead. Dispatch it with a station and the panel dimensions; it
estimates the depth map, meshes it, meshes a luminance version alongside for
comparison, uploads both STLs as artifacts, and commits the depth map back to
`model/source/`.

That gives you a first pass without installing anything. The hand-correction
step below still applies to what comes out.

### 3. Build the mesh

```sh
scripts/relief_from_heightmap.py depth.png -o panel.stl \
    --width-mm 150 --depth-mm 12 --base-mm 3
```

It produces a watertight solid — displaced front, flat back, side walls — and
refuses to write a mesh that is not closed or whose normals face inward. Useful
flags: `--resolution` (samples across the width; higher is finer and heavier),
`--gamma` (>1 deepens shadows), `--blur`, `--invert` for near=black depth maps.

To see the mechanics before you have a depth map, `--luminance` will build from
the photo directly. It will look wrong, in exactly the way described above.

### 4. Frame and backing

Model the Gothic frame **once** in Blender and reuse it for all fifteen — it is
the same frame in every panel, and this is what makes the set read as a series
regardless of the style shift at XI. Add a keyhole or a French cleat recess to
the backing plate while you are there.

---

## Path B — figures in the round (statues, nativity)

Three approaches, in increasing order of effort and quality:

**Single-image 3D reconstruction.** Feed the reference to an image-to-3D model
(TripoSR, TRELLIS, Hunyuan3D among the open ones; Meshy, Tripo and Rodin among
the hosted). Seconds to minutes, and you get a complete mesh. The catch is
consistent and matters here: the invented back is plausible but arbitrary, and
faces and hands come out soft — precisely the parts a devotional figure is
judged on. Treat the output as a **base mesh**, never as a finished model.

**Sculpting from reference.** Blender is free and entirely capable; Nomad
Sculpt on an iPad is inexpensive and pleasant for organic forms; ZBrush is the
professional standard. Realistically a day or more per figure once you are
practised.

**The hybrid, which is what most people should do.** Reconstruct a base mesh,
then sculpt the face, the hands, and the attributes by hand. It removes the
tedious blocking-out and keeps human judgement where it counts.

### Checking what comes back

Reconstruction output is usually watertight-ish and rarely print-ready. Run it
through the inspector before anything else:

```sh
scripts/inspect_mesh.py figure.stl
scripts/inspect_mesh.py figure.stl --fix clean.stl --fill-holes --drop-shells
```

It reports triangle count, bounding box, degenerate and duplicate faces, holes,
non-manifold edges, floating shells, and whether the normals face outward — then
repairs what it can. Two faults are worth knowing about in advance:

- **Scale is arbitrary.** These tools have no idea how big a saint is; the mesh
  comes out in nameless units. `--height-mm 180` rescales it to a real size.
- **Floating fragments.** Reconstruction often leaves stray shells drifting near
  the figure. `--drop-shells` keeps only the largest.

What the inspector cannot check is self-intersection and wall thickness. Take
those to the slicer, or Blender's 3D-Print Toolbox.

### Generating extra views

Since the references here are generated rather than photographed, you can ask
for the same figure from the side and the back and feed several views to a
multi-view reconstruction. It helps, but generated views drift — the fold of a
mantle will not agree between them — so treat the extra views as guidance for
sculpting rather than as photogrammetry input.

---

## Suggested first move

Do **one** station end to end at a small size before touching the other
fourteen: depth map, corrections, mesh, and a 100 mm test print. A single proof
teaches more about relief depth and detail loss than any amount of planning,
and everything learned goes into that station's **Print notes**, where the
other fourteen can use it.

Station XII is a good candidate — a strong central figure, a clear silhouette,
and few of the thin fragile features that make XI difficult.

## Decisions behind this pipeline

- [ADR-0005](adr/0005-depth-maps-not-luminance.md) — why depth maps, not luminance
- [ADR-0006](adr/0006-what-belongs-in-git.md) — why the STLs are not committed
- [ADR-0007](adr/0007-heavy-dependencies-run-in-ci.md) — why torch runs in CI
- [ADR-0009](adr/0009-hand-derived-test-fixtures.md) — why the fixtures are arithmetic

## Tooling

| | |
|---|---|
| Modelling | Blender (free), Nomad Sculpt (iPad), ZBrush |
| Depth maps | Depth Anything, Marigold, hosted equivalents |
| Image to 3D | TripoSR, TRELLIS, Hunyuan3D; Meshy, Tripo, Rodin |
| Mesh checks | Blender's 3D-Print Toolbox |
| Slicing | PrusaSlicer, OrcaSlicer, Bambu Studio, Cura |

Sizes, wall thicknesses, and mesh requirements are in
[`printing-guide.md`](printing-guide.md).
