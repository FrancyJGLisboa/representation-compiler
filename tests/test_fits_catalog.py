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
    assert payload["datasets"]["orion"]["metadata"]["input_frame"] == "ICRS"
    assert payload["datasets"]["orion"]["metadata"]["output_frame"] == "ICRS"
    assert payload["datasets"]["orion"]["metadata"]["longitude_unit"] == "deg"
    assert payload["frames"]["icrs-cartesian"]["reference"] == "ICRS"


def test_fits_catalog_rejects_unsupported_frame(tmp_path):
    source = tmp_path / "unknown-frame.fits"
    make_catalog(source, "ECLIPTIC")

    with pytest.raises(ValueError, match="ICRS, FK5, FK4, or GALACTIC"):
        import_icrs_fits_catalog(source, ra_column="RA", dec_column="DEC")


def test_galactic_fits_coordinates_are_transformed_to_icrs(tmp_path):
    source = tmp_path / "galactic-center.fits"
    table = Table()
    table["L"] = [0.0] * u.deg
    table["B"] = [0.0] * u.deg
    table.write(source)
    with fits.open(source, mode="update") as hdul:
        hdul[1].header["RADESYS"] = "GALACTIC"

    payload = import_icrs_fits_catalog(source, ra_column="L", dec_column="B").notebook.to_dict()
    point = payload["derived_data"]["icrs-unit-vectors"]["rows"][0]

    assert point["ra_deg"] == pytest.approx(266.4051, abs=0.001)
    assert point["dec_deg"] == pytest.approx(-28.9362, abs=0.001)
    assert payload["datasets"]["galactic-center"]["metadata"]["input_frame"] == "GALACTIC"
    assert payload["datasets"]["galactic-center"]["metadata"]["output_frame"] == "ICRS"


@pytest.mark.parametrize(("frame", "equinox"), [("FK5", 2000.0), ("FK4", 1950.0)])
def test_equatorial_fits_frames_are_transformed_to_icrs(tmp_path, frame, equinox):
    source = tmp_path / f"{frame.lower()}.fits"
    make_catalog(source, frame)
    with fits.open(source, mode="update") as hdul:
        hdul[1].header["EQUINOX"] = equinox

    payload = import_icrs_fits_catalog(source, ra_column="RA", dec_column="DEC").notebook.to_dict()
    point = payload["derived_data"]["icrs-unit-vectors"]["rows"][0]

    assert point["ra_deg"] != pytest.approx(83.822, abs=1e-10)
    assert payload["datasets"][frame.lower()]["metadata"]["input_frame"] == frame
    assert payload["frames"]["icrs-cartesian"]["epoch"] == "J2000"
