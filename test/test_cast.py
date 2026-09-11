import math
from pathlib import Path

from osgeo import gdal, ogr

from algorithms.casting import apply_constant, apply_tin


class TestCasting:
    """Smoke tests for the casting pipeline."""

    def test_full_pipeline_dem(self, tmp_path: Path) -> None:
        data_dir = Path(__file__).parent / "data"
        gpkg_path = data_dir / "example.gpkg"
        raster_path = data_dir / "dem.tif"
        output_path = "output.tif"

        ogr.UseExceptions()
        gpkg_ds = ogr.Open(str(gpkg_path))
        raster_ds = gdal.Open(str(raster_path))
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.CreateCopy(str(output_path), raster_ds)

        # Set nodata value
        band = out_ds.GetRasterBand(1)
        band.SetNoDataValue(-9999.0)

        surface_layer = gpkg_ds.GetLayerByName("surface")
        pixel_size = abs(raster_ds.GetGeoTransform()[1])

        apply_constant(str(gpkg_path), out_ds)
        apply_tin(gpkg_ds, surface_layer, out_ds, pixel_size)

    def test_full_pipeline_no_dem(self, tmp_path: Path) -> None:
        data_dir = Path(__file__).parent / "data"
        gpkg_path = data_dir / "example.gpkg"
        output_path = "output_no_dem.tif"

        ogr.UseExceptions()
        gpkg_ds = ogr.Open(str(gpkg_path))
        surface_layer = gpkg_ds.GetLayerByName("surface")
        srs = surface_layer.GetSpatialRef()
        pixel_size = 0.5

        # Create base raster
        min_x, max_x, min_y, max_y = (
            surface_layer.GetExtent()
        )  # (minX, maxX, minY, maxY)
        cols = math.ceil((max_x - min_x) / pixel_size)
        rows = math.ceil((max_y - min_y) / pixel_size)
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(output_path, cols, rows, 1, gdal.GDT_Float32)
        out_ds.SetGeoTransform((min_x, pixel_size, 0, max_y, 0, -pixel_size))
        out_ds.SetProjection(srs.ExportToWkt())
        band = out_ds.GetRasterBand(1)
        band.SetNoDataValue(-9999.0)

        apply_constant(str(gpkg_path), out_ds)
        apply_tin(gpkg_ds, surface_layer, out_ds, pixel_size)

    def test_full_pipeline_holes(self, tmp_path: Path) -> None:
        data_dir = Path(__file__).parent / "data"
        gpkg_path = data_dir / "example_holes.gpkg"
        output_path = "output_no_dem_holes.tif"

        ogr.UseExceptions()
        gpkg_ds = ogr.Open(str(gpkg_path))
        surface_layer = gpkg_ds.GetLayerByName("surface")
        srs = surface_layer.GetSpatialRef()
        pixel_size = 0.5
        distance = 2.0

        # Create base raster
        min_x, max_x, min_y, max_y = (
            surface_layer.GetExtent()
        )  # (minX, maxX, minY, maxY)
        cols = math.ceil((max_x - min_x) / pixel_size)
        rows = math.ceil((max_y - min_y) / pixel_size)
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(output_path, cols, rows, 1, gdal.GDT_Float32)
        out_ds.SetGeoTransform((min_x, pixel_size, 0, max_y, 0, -pixel_size))
        out_ds.SetProjection(srs.ExportToWkt())
        band = out_ds.GetRasterBand(1)
        band.SetNoDataValue(-9999.0)

        apply_constant(str(gpkg_path), out_ds)
        apply_tin(gpkg_ds, surface_layer, out_ds, distance)
