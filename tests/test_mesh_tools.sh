#!/usr/bin/env bash
# Fixture tests for scripts/inspect_mesh.py and scripts/relief_from_heightmap.py.
# Every expected value is derived by hand, not captured from the code's own output.
#
#   tests/test_mesh_tools.sh
set -u
cd "$(dirname "$0")/.."
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
fail=0

chk() {  # chk <name> <actual> <expected>
  if [ "$2" = "$3" ]; then echo "  PASS  $1"
  else echo "  FAIL  $1: got '$2' want '$3'"; fail=1; fi
}

python3 - "$TMP" <<'PY'
import numpy as np, sys
sys.path.insert(0, "scripts")
from inspect_mesh import write_stl
from pathlib import Path
T = Path(sys.argv[1])

# 10 mm cube, outward winding -> exactly 1000 mm3
v = np.array([[0,0,0],[10,0,0],[10,10,0],[0,10,0],
              [0,0,10],[10,0,10],[10,10,10],[0,10,10]], float)
f = np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],
              [1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
write_stl(T/"clean.stl", v, f)
write_stl(T/"hole.stl", v, f[:-2])                 # one wall missing
write_stl(T/"inverted.stl", v, f[:, [0,2,1]])      # every normal inward
mixed = f.copy(); mixed[[2,5,7,10]] = mixed[[2,5,7,10]][:, [0,2,1]]
write_stl(T/"mixed.stl", v, mixed)                 # 4 of 12 backwards
write_stl(T/"dupes.stl", v, np.vstack([f, f[:3], [[0,0,1],[2,2,2]]]))
write_stl(T/"shells.stl", np.vstack([v, v+[40,0,0]]), np.vstack([f, f+8]))

tri = v[f]
lines = ["solid t"]
for t in tri:
    lines += ["facet normal 0 0 0", " outer loop"] + [f"  vertex {x} {y} {z}" for x,y,z in t] + [" endloop","endfacet"]
(T/"ascii.stl").write_text("\n".join(lines + ["endsolid t"]))
PY

I="python3 scripts/inspect_mesh.py"
echo "inspect_mesh"
chk "clean cube is 1 cm3"        "$($I $TMP/clean.stl | grep 'signed volume' | awk '{print $3}')" "1.00"
chk "clean cube is watertight"   "$($I $TMP/clean.stl | grep 'watertight' | awk '{print $2}')" "yes"
chk "missing wall = 4 bnd edges" "$($I $TMP/hole.stl | grep 'boundary edges' | awk '{print $3}')" "4"
chk "hole filled back to 1 cm3"  "$($I $TMP/hole.stl --fix $TMP/a.stl --fill-holes | grep '^  volume' | awk '{print $2}')" "1.00"
chk "inverted detected"          "$($I $TMP/inverted.stl | grep 'signed volume' | awk '{print $3}')" "-1.00"
chk "inverted repaired"          "$($I $TMP/inverted.stl --fix $TMP/b.stl | grep '^  volume' | awk '{print $2}')" "1.00"
chk "mixed winding detected"     "$($I $TMP/mixed.stl | grep 'signed volume' | awk '{print $3}')" "0.33"
chk "mixed winding repaired"     "$($I $TMP/mixed.stl --fix $TMP/c.stl | grep '^  volume' | awk '{print $2}')" "1.00"
chk "junk faces stripped"        "$($I $TMP/dupes.stl --fix $TMP/d.stl | grep '^  triangles' | tail -1 | awk '{print $2}')" "12"
chk "two shells counted"         "$($I $TMP/shells.stl | grep '^  shells ' | awk '{print $2}')" "2"
chk "smaller shell dropped"      "$($I $TMP/shells.stl --fix $TMP/e.stl --drop-shells | grep '^  volume' | awk '{print $2}')" "1.00"
chk "ascii stl read"             "$($I $TMP/ascii.stl | grep '^  triangles' | awk '{print $2}')" "12"
# scale must ignore vertices belonging to a dropped shell
chk "scale after shell drop"     "$($I $TMP/shells.stl --fix $TMP/f.stl --drop-shells --height-mm 180 | grep 'bounding box' | tail -1 | awk '{print $3}')" "180.00"

echo "relief_from_heightmap"
cat > "$TMP/relief_check.py" <<'PYEOF'
import numpy as np, sys
sys.path.insert(0, "scripts")
from relief_from_heightmap import build_relief, is_manifold, signed_volume
# flat 4 x 5 x 1 mm plate -> exactly 20 mm3 by hand
v, f = build_relief(np.zeros((6, 5)), width_mm=4.0, depth_mm=0.0, base_mm=1.0)
print(f"{signed_volume(v, f):.3f}")
print("yes" if is_manifold(f)[0] else "no")
# half-raised plate: 30 x 40.34 base 2mm + 30 x 20 raised 10mm ~ 8.5 cm3
h = np.zeros((40, 30)); h[:20, :] = 1.0
v2, f2 = build_relief(h, width_mm=30.0, depth_mm=10.0, base_mm=2.0)
print("yes" if is_manifold(f2)[0] else "no")
print(f"{signed_volume(v2, f2) / 1000:.1f}")
PYEOF
python3 "$TMP/relief_check.py" > "$TMP/relief_out.txt"
chk "flat plate volume"          "$(sed -n 1p "$TMP/relief_out.txt")" "20.000"
chk "flat plate manifold"        "$(sed -n 2p "$TMP/relief_out.txt")" "yes"
chk "stepped plate manifold"     "$(sed -n 3p "$TMP/relief_out.txt")" "yes"
chk "stepped plate volume"       "$(sed -n 4p "$TMP/relief_out.txt")" "8.5"

echo
if [ $fail -eq 0 ]; then echo "All tests passed."; else echo "FAILURES"; fi
exit $fail
