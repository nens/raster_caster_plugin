from pathlib import Path

from osgeo import gdal, ogr

from algorithms.casting import apply_constant, apply_tin


class TestCasting:
    """Smoke tests for the casting pipeline."""

    def test_full_pipeline(self, tmp_path: Path) -> None:
        data_dir = Path(__file__).parent / "data"
        gpkg_path = data_dir / "example.gpkg"
        raster_path = data_dir / "dem.tif"
        output_path = tmp_path / "output.tif"

        ogr.UseExceptions()
        gpkg_ds = ogr.Open(str(gpkg_path))
        raster_ds = gdal.Open(str(raster_path))
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.CreateCopy(str(output_path), raster_ds)

        surface_layer = gpkg_ds.GetLayerByName("surface")
        pixel_size = abs(raster_ds.GetGeoTransform()[1])

        apply_constant(str(gpkg_path), out_ds)
        apply_tin(gpkg_ds, surface_layer, out_ds, pixel_size)

        out_ds = None
        raster_ds = None
        gpkg_ds = None
