import json

import pytest

astropy = pytest.importorskip("astropy")
from astropy import units as u
from astropy.io import fits
from astropy.table import Table

from representation_compiler.fits_catalog import import_icrs_fits_catalog


def make_catalog(path, frame="ICRS"):
    table = Table()
    table["RA"] = [83.822, 78.634] * u.deg
    table["DEC"] = [-5.391, -8.202] * u.deg
    table.write(path)
    with fits.open(path, mode="update") as hdul:
        hdul[1].header["RADESYS"] = frame
        hdul[1].header["EQUINOX"] = 2000.0


def test_fits_catalog_records_explicit_units_and_frame(tmp_path):
    source = tmp_path / "orion.fits"
    make_catalog(source)

    imported = import_icrs_fits_catalog(source, ra_column="RA", dec_column="DEC")
    output = imported.notebook.write_json(tmp_path / "orion.notebook.json")
    payload = json.loads(output.read_text())

    assert imported.row_count == 2
    assert payload["datasets"]["orion"]["format"] == "fits"
    assert payload["datasets"]["orion"]["metadata"]["radesys"] == "ICRS"
    assert payload["datasets"]["orion"]["metadata"]["ra_unit"] == "deg"
    assert payload["frames"]["icrs-cartesian"]["reference"] == "ICRS"


def test_fits_catalog_rejects_missing_or_non_icrs_frame(tmp_path):
    source = tmp_path / "unknown-frame.fits"
    make_catalog(source, "FK5")

    with pytest.raises(ValueError, match="explicit ICRS frame"):
        import_icrs_fits_catalog(source, ra_column="RA", dec_column="DEC")
