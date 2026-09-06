# Nativity — Set 01

The first presépio. No pieces yet.

## Scale comes first

A nativity is the one collection where the pieces must agree with each other.
A shepherd modelled at a different scale from the Magi ruins the crib no matter
how well each prints. Set `scale.figure_height_mm` in `metadata.json` before
modelling anything — the height of a standing adult figure — and proportion
every other piece from it. Home cribs usually sit between 70 and 200 mm.

Kneeling figures, the Infant, and the animals are sized *relative* to that
figure, not printed to the same height.

## Adding pieces

Same as statues:

```sh
scripts/new_piece.py collections/nativity/set-01 "Saint Joseph" --feast "19 March"
scripts/import_images.py collections/nativity/set-01 --move
```

## A usual first set

The Holy Family (the Infant in the manger, Our Lady, Saint Joseph), the ox and
the ass, the shepherds, the Magi with their gifts, an angel, and the stable
itself. The stable is usually printed in sections and is worth modelling last,
once the figures fix its size.
