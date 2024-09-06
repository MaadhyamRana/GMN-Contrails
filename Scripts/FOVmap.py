""" Produces a map for all FL, for all stations in North America and Europe """

import os
import sys

try:
    from fastkml import kml
    from pygeoif.geometry import Polygon
    import folium
    import geopandas as gpd

except ModuleNotFoundError as m:
    print(f"{m}\nExiting...")
    sys.exit()

MAPFILE_NAME = "FOVMap.html"
KML_SRC = os.path.join(os.getcwd(), "FOVall")
if not os.path.exists(KML_SRC):
    print(f"FOV KMLs not found at {KML_SRC}, please run FOVall.py in current directory.\nExiting...")
    sys.exit()

FLIGHT_LEVELS = ['FL280', 'FL290', 'FL300',
                 'FL310', 'FL320', 'FL330',
                 'FL340', 'FL350', 'FL360',
                 'FL370', 'FL380', 'FL390',
                 'FL400', 'FL410', 'FL420',
                 'FL430', 'FL440', 'FL450']

NA = ["CA", "US", "MX"]
EU = ["AT", "BE", "BG", "HR", "CZ",
      "DK", "FI", "FR", "DE", "GR",
      "HU", "IE", "IT", "LU", "NL",
      "PL", "PT", "RO", "RU", "SK",
      "SI", "ES", "CH", "UA", "UK"]

STATIONS = NA + EU


def FOVmap():
    """ Creates a map for all FL, for all stations in North America and Europe

    Returns
    -------
        Creates an HTML file in working directory with the folium map
    """

    folium_map = folium.Map(location = [50.0, -50.0], zoom_start = 4)

    for flight_level in FLIGHT_LEVELS:

        # Browse the North American and European stations for KMLs at current fl
        stations = [d for d in os.listdir(KML_SRC) if (d[:2] in STATIONS)]
        polygons = []

        for station in stations:

            # Parse KML file
            with open(os.path.join(KML_SRC, f"{station}/{station}-{flight_level}.kml"), 'rt') as f:
                kml_content = f.read()
            k = kml.KML()
            k.from_string(kml_content.encode('utf-8'))

            # Flatten 3D polygons to 2D
            # The KML placemark is arranged as MultiGeometry > Polygon > LinearRing
            for feature in list(k.features()):
                for placemark in list(feature.features()):
                    for polygon in placemark.geometry.geoms:
                        flat_coords = [(x, y) for x, y, z in polygon.exterior.coords]
                        polygons.append(Polygon(flat_coords))

        # Convert polygons to a GeoDataFrame - corresponding stations and polygons
        # are stored in corresponding lists
        gdf = gpd.GeoDataFrame({'Station name: ': stations, 'geometry': polygons})
        gdf.set_crs(epsg=4326, inplace=True)  # WGS84 system

        # Add polygons from current flight level to a folium feature group
        # The map by default, shows only FL280 at initialization
        feature_group = folium.FeatureGroup(name=flight_level, show=(True and flight_level == "FL280"))

        # Folium GeoJson object - all polygon visuals are managed here
        folium.GeoJson(
            gdf,
            name=flight_level,
            style_function=lambda feature: {
                'fillColor': 'blue',
                'color': 'white',
                'weight': 0.5,
                'fillOpacity': 0.15,
            },
            highlight_function=lambda feature: {
                'fillColor': 'red',
            },
            popup_keep_highlighted=True,
            zoom_on_click=True,
            popup=folium.GeoJsonPopup(fields = ['Station name: '])
        ).add_to(feature_group)

        feature_group.add_to(folium_map)

    # Add LayerControl to switch between layers and save map
    folium.LayerControl().add_to(folium_map)
    folium_map.save(MAPFILE_NAME)


if __name__ == "__main__":
    FOVmap()
