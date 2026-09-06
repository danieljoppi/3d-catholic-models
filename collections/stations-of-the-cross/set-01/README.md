# Stations of the Cross — Set 01

The first Via Crucis series: the 14 traditional stations plus the
Resurrection, 15 images in all.

## Source

Google Photos album: <https://photos.app.goo.gl/EdYMHR8VvGUWcRZD9>

**The images are not yet in this repository.** The album host is not
reachable from the environment this structure was created in, so the folders,
metadata, and import tooling are in place and waiting for the files.

## Importing the images

1. Open the album and download all 15 images (Google Photos: ⋮ → *Download all*).
2. Unzip them into `_inbox/` in this directory.
3. From the repository root:

   ```sh
   scripts/import_stations.py collections/stations-of-the-cross/set-01 --dry-run
   ```

   Check the mapping it prints — station order matters more than filenames.
4. Re-run without `--dry-run` to import. Add `--move` to empty `_inbox/`,
   or `--by-order` if the filenames contain numbers that are not station
   numbers.

The script renames each image to its station, files it under
`stations/<NN-slug>/reference/`, and records it in `metadata.json`.

## Stations

| # | Station | Português |
|---|---|---|
| 1 | Jesus is condemned to death | Jesus é condenado à morte |
| 2 | Jesus carries His cross | Jesus carrega a cruz |
| 3 | Jesus falls the first time | Jesus cai pela primeira vez |
| 4 | Jesus meets His mother | Jesus encontra sua Mãe |
| 5 | Simon of Cyrene helps Jesus carry the cross | Simão Cireneu ajuda Jesus a carregar a cruz |
| 6 | Veronica wipes the face of Jesus | Verônica enxuga o rosto de Jesus |
| 7 | Jesus falls the second time | Jesus cai pela segunda vez |
| 8 | Jesus meets the women of Jerusalem | Jesus consola as mulheres de Jerusalém |
| 9 | Jesus falls the third time | Jesus cai pela terceira vez |
| 10 | Jesus is stripped of His garments | Jesus é despojado das vestes |
| 11 | Jesus is nailed to the cross | Jesus é pregado na cruz |
| 12 | Jesus dies on the cross | Jesus morre na cruz |
| 13 | Jesus is taken down from the cross | Jesus é descido da cruz |
| 14 | Jesus is laid in the tomb | Jesus é sepultado |
| 15 | The Resurrection of the Lord | A Ressurreição do Senhor |

## Rights

The artist and licence of the source artwork are still `TODO` in
`metadata.json`. Fill them in before publishing or sharing any model derived
from these images.
