from typing import Any

import numpy as np
from osgeo import gdal, ogr

from .utils import periodic_linear_interp


def apply_constant(gpkg_path: str, out_ds: Any) -> None:
    gdal.Rasterize(
        out_ds,
        gpkg_path,
        layers=["surface"],
        attribute="param_1",
        where="definition_type = 'constant'",
    )


def apply_tin(gpkg_ds: Any, layer: Any, out_ds: Any, pixel_size: float) -> None:
    layer.SetAttributeFilter("definition_type = 'tin'")
    tin_surface_features = [f for f in layer]
    layer.SetAttributeFilter(None)

    # band = out_ds.GetRasterBand(1)
    elev_point_layer = gpkg_ds.GetLayerByName("elevation_point")

    # TODO: add in_polygon_only feature
    for tin_surface in tin_surface_features:
        # retrieve the elevation points in the tin surface geometry
        # and convert to PolygonZ
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
                    f.GetGeometryRef().GetZ(),
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
                exterior.GetPoint(index)[:2]
                for index in range(exterior.GetPointCount() - 1)
            ]
        )
        distances = elev_coords[:, None, :2] - tin_vertices[None, :, :]
        nearest_vertex_indices = np.argmin(
            np.sum(distances * distances, axis=2), axis=1
        )

        # Replace each nearest exterior vertex Z-value with the elevation point Z-value.
        closing_point_index = exterior.GetPointCount() - 1
        for elevation_point, vertex_index in zip(elev_coords, nearest_vertex_indices):
            x, y, z = exterior.GetPoint(int(vertex_index))
            exterior.SetPoint(int(vertex_index), x, y, elevation_point[2])
            if vertex_index == 0:
                # The exterior ring is closed, update both start and end
                exterior.SetPoint(closing_point_index, x, y, elevation_point[2])

        vertex_z = np.array(
            [exterior.GetPoint(index)[2] for index in range(len(tin_vertices))]
        )
        edge_lengths = np.linalg.norm(
            np.roll(tin_vertices, -1, axis=0) - tin_vertices,
            axis=1,
        )
        arc_lengths = np.concatenate(([0.0], np.cumsum(edge_lengths[:-1])))
        perimeter = float(np.sum(edge_lengths))
        known_vertices = vertex_z != -9999.0

        if perimeter > 0 and np.any(known_vertices):
            vertex_z[~known_vertices] = periodic_linear_interp(
                arc_lengths[~known_vertices],
                arc_lengths[known_vertices],
                vertex_z[known_vertices],
                period=perimeter,
            )
            for vertex_index, z in enumerate(vertex_z):
                x, y, _ = exterior.GetPoint(vertex_index)
                exterior.SetPoint(vertex_index, x, y, z)
            x, y, _ = exterior.GetPoint(0)
            exterior.SetPoint(closing_point_index, x, y, vertex_z[0])
