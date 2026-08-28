# Astronomy Representation Notebook

## The job to be done

An astronomer should be able to turn an observation, catalog, model, or paper into a shareable representation that makes one scientific relationship easier to reason about—and lets another person verify, alter, and extend it.

This is not “make a sky-map diagram.” It is:

```text
dataset + coordinate frame + transformation + assumptions + test
→ interactive scientific explanation
→ forkable representation notebook
```

## First executable slice

The initial notebook contract lives in `representation_compiler.notebook`.

- `DatasetReference` records the source and checksum.
- `CoordinateFrame` records axes, units, epoch, and reference frame.
- `Representation` records encoding/decoding, information preserved/discarded, what becomes easier, interactive controls, and linked tests.
- `RepresentationTest` records a falsifiable statement and its result.
- `RepresentationNotebook` validates that a shareable notebook is self-describing.

`representation_compiler.astronomy` provides the first real transformation: ICRS right ascension/declination in degrees to a Cartesian unit vector. It explicitly preserves angular direction and great-circle geometry while discarding radial distance and brightness. Its first test verifies that the encoded direction has unit norm.

## What makes this different from a chat response

A chat can suggest a coordinate transformation. A notebook makes the transformation inspectable and reusable:

1. A recipient sees the dataset and frame it assumes.
2. They can run the same mapping and test the stated invariant.
3. They can compare it with another representation, such as a sky projection, phase space, light curve, or graph.
4. They can fork the notebook, change an assumption, and publish their result.

## Import a CSV catalog now

The importer requires the explicit degree columns `ra_deg` and `dec_deg`; it will not guess units from ambiguous `ra` and `dec` headers.

```bash
python3 -m representation_compiler.cli \
  --import-star-catalog catalog.csv \
  --catalog-source-uri "https://archive.example.org/catalog.csv" \
  --notebook-output catalog.notebook.json
```

The JSON records the source checksum, row count, ICRS Cartesian frame, reversible mapping, what the representation preserves/discards, and a passed unit-norm test over every imported coordinate.

## Next build slice

Add portable derived vector data and an interactive sky explorer. FITS support comes after this contract is proven with real catalogs.
