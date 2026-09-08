from typing import Any

import numpy as np
from osgeo import gdal, ogr
from osgeo.gdal import ApplyGeoTransform, InvGeoTransform
from scipy.interpolate import LinearNDInterpolator
from shapely import constrained_delaunay_triangles, from_wkb
from shapely.geometry import Point

from .utils import periodic_linear_interp


def apply_constant(gpkg_path: str, out_ds: Any) -> None:
    gdal.Rasterize(
        out_ds,
        gpkg_path,
        layers=["surface"],
        attribute="param_1",
        where="definition_type = 'constant'",
    )


def apply_tin(gpkg_ds: Any, layer: Any, out_ds: Any, pixel_size: float) -> bool:
    # Retrieve tin surfaces
    layer.SetAttributeFilter("definition_type = 'tin'")
    tin_surface_features = [f for f in layer]
    layer.SetAttributeFilter(None)

    elev_point_layer = gpkg_ds.GetLayerByName("elevation_point")

    # TODO: add in_polygon_only feature
    for tin_surface in tin_surface_features:
        # Convert surface to PolygonZ
        tin_geom = tin_surface.GetGeometryRef()
        polygon_z = ogr.Geometry(ogr.wkbPolygon25D)
        for ring_index in range(tin_geom.GetGeometryCount()):
            source_ring = tin_geom.GetGeometryRef(ring_index)
            ring_z = ogr.Geometry(ogr.wkbLinearRing)
            for point_index in range(source_ring.GetPointCount()):
                x, y, _ = source_ring.GetPoint(point_index)
                ring_z.AddPoint(x, y, -9999.0)
            polygon_z.AddGeometry(ring_z)
        tin_geom = polygon_z

        # Get the elevation points in the polygon TODO: with buffer?
        elev_point_layer.SetSpatialFilter(tin_geom.Buffer(pixel_size))
        elev_coords = np.array(
            [
                (
                    f.GetGeometryRef().GetX(),
                    f.GetGeometryRef().GetY(),
                    f[
                        "elevation"
                    ],  # Note that this is not the Z, but attribute "elevation"
                )
                for f in elev_point_layer
            ]
        )
        elev_point_layer.SetSpatialFilter(None)

        if len(elev_coords) < 3:
            continue

        # Associate the elev_coords points with nearest vertices for exterior
        exterior = tin_geom.GetGeometryRef(0)  # 0 is exterior?
        tin_vertices = np.array(
            [
                exterior.GetPoint(index)[:2]  # drop Z
                for index in range(exterior.GetPointCount() - 1)
            ]
        )
        # Use 2D for distance
        elev_xy = elev_coords[:, :2]  # drop Z
        # newaxis allows for broadcasting:
        # (distances[i, j] = elev_xy[i] - tin_vertices[j])
        distances = elev_xy[:, np.newaxis] - tin_vertices[np.newaxis, :]
        # Sum the squared x-distance and y-distance, and take the minimum
        nearest_vertex_indices = np.argmin(
            np.sum(distances * distances, axis=2), axis=1
        )
        for elevation_point, vertex_index in zip(elev_coords, nearest_vertex_indices):
            print(elevation_point[:2], tin_vertices[vertex_index])

        # Replace each nearest exterior vertex Z-value with the elevation point
        # value (Note that this is not the Z-value, but the attribute value
        closing_point_index = exterior.GetPointCount() - 1
        for elevation_point, vertex_index in zip(elev_coords, nearest_vertex_indices):
            x, y, z = exterior.GetPoint(int(vertex_index))
            exterior.SetPoint(int(vertex_index), x, y, elevation_point[2])
            if vertex_index == 0:
                # The exterior ring is closed, update both start and end
                exterior.SetPoint(closing_point_index, x, y, elevation_point[2])

        # Determine the individual segment lengths and perimenter of the geometry by
        # determining the norm between a vertex and the previous
        # validated in QGIS with Measurement tool (extract vertices)
        edge_lengths = np.linalg.norm(
            np.roll(tin_vertices, -1, axis=0) - tin_vertices,
            axis=1,
        )
        # Validated in QGIS with $perimeter
        perimeter = float(np.sum(edge_lengths))

        tin_vertices_z = np.array(
            [exterior.GetPoint(index)[2] for index in range(len(tin_vertices))]
        )
        known_vertices_mask = tin_vertices_z != -9999.0
        # Calculate the distance along the polygon perimeter to the start of each
        # vertex.
        # Take cumulutive sum up to second last edge, prepend with 0.0 for first vertex
        # Note that the final arc (returning to first vertex) is excluded.
        arc_lengths = np.concatenate(([0.0], np.cumsum(edge_lengths[:-1])))
        if perimeter > 0 and np.any(known_vertices_mask):
            tin_vertices_z[~known_vertices_mask] = periodic_linear_interp(
                arc_lengths[~known_vertices_mask],
                arc_lengths[known_vertices_mask],
                tin_vertices_z[known_vertices_mask],
                period=perimeter,
            )
            # Set the newly calculated elevations to the geometry
            for vertex_index, z in enumerate(tin_vertices_z):
                x, y, _ = exterior.GetPoint(vertex_index)
                exterior.SetPoint(vertex_index, x, y, z)
            x, y, _ = exterior.GetPoint(0)
            exterior.SetPoint(closing_point_index, x, y, tin_vertices_z[0])

        # Determine constrained delaunay triangulation
        shapely_polygon = from_wkb(bytes(tin_geom.ExportToWkb()))
        triangles = constrained_delaunay_triangles(shapely_polygon)

        # # TEST Create triangles geopackage
        # triangles_gpkg = None
        # triangles_layer = None
        # driver = ogr.GetDriverByName("GPKG")
        # triangles_gpkg = driver.CreateDataSource("triangles.gpkg")
        # triangles_layer = triangles_gpkg.CreateLayer(
        #     "triangles", geom_type=ogr.wkbPolygon
        # )
        # for triangle in triangles.geoms:
        #     feature = ogr.Feature(triangles_layer.GetLayerDefn())
        #     triangle_ogr = ogr.CreateGeometryFromWkb(triangle.wkb)
        #     feature.SetGeometry(triangle_ogr)
        #     triangles_layer.CreateFeature(feature)
        # triangles_gpkg = None
        # print(triangles)

        # Apply interpolation to raster
        band = out_ds.GetRasterBand(1)
        band.SetNoDataValue(-9999.0)
        geotransform = out_ds.GetGeoTransform()
        minx, px_width, _, maxy, _, px_height = geotransform
        raster_array = band.ReadAsArray()

        for triangle in triangles.geoms:
            coords = list(triangle.exterior.coords)[:-1]
            if len(coords) != 3:
                return False

            tri_points = np.array([(coord[0], coord[1]) for coord in coords])
            tri_z = np.array([coord[2] for coord in coords])
            interp = LinearNDInterpolator(tri_points, tri_z, fill_value=-9999.0)

            # Convert triangle bounds to raster pixel coordinates
            min_tri_x, min_tri_y, max_tri_x, max_tri_y = triangle.bounds
            inv_geotransform = InvGeoTransform(geotransform)

            col_start_float, row_start_float = ApplyGeoTransform(
                inv_geotransform, min_tri_x, max_tri_y
            )
            col_end_float, row_end_float = ApplyGeoTransform(
                inv_geotransform, max_tri_x, min_tri_y
            )

            # Clamping to prevent setting of pixels outside the raster
            col_start = max(0, int(np.floor(col_start_float)) - 1)
            col_end = min(raster_array.shape[1], int(np.ceil(col_end_float)) + 1)
            row_start = max(0, int(np.floor(row_start_float)) - 1)
            row_end = min(raster_array.shape[0], int(np.ceil(row_end_float)) + 1)

            for row in range(row_start, row_end):
                for col in range(col_start, col_end):
                    # Test pixel centers so values outside the triangle are untouched.
                    px_x = minx + (col + 0.5) * px_width
                    px_y = maxy + (row + 0.5) * px_height
                    if triangle.covers(Point(px_x, px_y)):
                        raster_array[row, col] = interp(px_x, px_y)

        band.WriteArray(raster_array)
    return True
