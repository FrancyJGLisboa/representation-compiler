"""Optional Astropy-backed FITS catalog import with explicit coordinate semantics."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .astronomy import ICRSSkyPoint, icrs_unit_vector, norm
from .catalog import CatalogImport, _slug
from .notebook import CoordinateFrame, DatasetReference, DerivedData, Representation, RepresentationNotebook, RepresentationTest


def import_icrs_fits_catalog(
    path: str | Path, *, ra_column: str, dec_column: str, hdu: int = 1, frame: str | None = None, source_uri: str | None = None,
) -> CatalogImport:
    """Import a FITS binary table whose specified RA/Dec columns have units convertible to degrees."""
    try:
        from astropy import units as u
        from astropy.io import fits
        from astropy.table import Table
    except ImportError as error:
        raise RuntimeError("FITS import requires `python3 -m pip install -e '.[astronomy]'`") from error

    source = Path(path)
    with fits.open(source) as hdul:
        header = hdul[hdu].header
        table = Table.read(source, hdu=hdu)
    if ra_column not in table.colnames or dec_column not in table.colnames:
        raise ValueError(f"FITS table must contain requested columns: {ra_column}, {dec_column}")
    declared_frame = (frame or header.get("RADESYS") or "").strip().upper()
    if declared_frame != "ICRS":
        raise ValueError("FITS catalog requires explicit ICRS frame via RADESYS=ICRS or --fits-frame ICRS")
    try:
        right_ascension = u.Quantity(table[ra_column]).to_value(u.deg)
        declination = u.Quantity(table[dec_column]).to_value(u.deg)
    except Exception as error:
        raise ValueError("FITS RA and Dec columns must declare units convertible to degrees") from error
    if len(right_ascension) != len(declination) or not len(right_ascension):
        raise ValueError("FITS RA and Dec columns must contain the same non-zero number of rows")
    vectors, rows = [], []
    for index, (ra, dec) in enumerate(zip(right_ascension, declination), start=1):
        try:
            point = ICRSSkyPoint(float(ra), float(dec))
            vector = icrs_unit_vector(point)
        except ValueError as error:
            raise ValueError(f"FITS row {index}: invalid ICRS coordinates: {error}") from error
        vectors.append(vector)
        rows.append({"id": f"row-{index}", "ra_deg": point.right_ascension_deg, "dec_deg": point.declination_deg, "x": vector[0], "y": vector[1], "z": vector[2]})
    max_error = max(abs(norm(vector) - 1) for vector in vectors)
    dataset_id = _slug(source.stem) or "fits-catalog"
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    epoch = str(header.get("EQUINOX", ""))
    notebook = RepresentationNotebook(
        id=f"{dataset_id}-unit-sphere",
        title=f"{source.stem}: ICRS unit-sphere representation",
        question="Which angular relationships in this FITS catalog become easier to reason about in Cartesian coordinates?",
        datasets={dataset_id: DatasetReference(dataset_id, source.name, source_uri or f"file://{source.name}", "fits", f"sha256:{checksum}", metadata={"row_count": str(len(rows)), "ra_column": ra_column, "dec_column": dec_column, "ra_unit": str(table[ra_column].unit), "dec_unit": str(table[dec_column].unit), "radesys": declared_frame, "equinox": epoch, "hdu": str(hdu)})},
        frames={"icrs-cartesian": CoordinateFrame("icrs-cartesian", "ICRS Cartesian unit sphere", ("x", "y", "z"), ("unit", "unit", "unit"), epoch, declared_frame)},
        tests={"unit-norm": RepresentationTest("unit-norm", "Every ICRS direction encodes to a unit Cartesian vector", "Compute max(abs(norm(vector) - 1)) over FITS rows", "passed", f"{len(rows)} rows checked; maximum norm error = {max_error:.3g}")},
        representations={"unit-sphere": Representation("unit-sphere", "ICRS unit sphere", "coordinate transformation", (dataset_id,), "icrs-cartesian", "(RA, Dec) in declared degree units → unit Cartesian vector", "unit Cartesian vector → (RA, Dec)", ("angular direction", "great-circle geometry", "rotation-invariant angular comparison"), ("radial distance", "brightness", "FITS row order"), ("angular separation", "vector-based sky rotations", "spatial indexing"), ("select object", "rotate sky"), ("unit-norm",), "icrs-unit-vectors")},
        derived_data={"icrs-unit-vectors": DerivedData("icrs-unit-vectors", "unit-sphere", ("id", "ra_deg", "dec_deg", "x", "y", "z"), tuple(rows))},
    )
    notebook.validate()
    return CatalogImport(notebook, len(rows), max_error)
