import os
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd


KMZ_FOLDER = "kmz"
GEOJSON_FOLDER = "geojson"


def extraer_kml_desde_kmz(kmz_path: str) -> str:
    temp_dir = tempfile.mkdtemp()

    with zipfile.ZipFile(kmz_path, "r") as z:
        z.extractall(temp_dir)

    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.lower().endswith(".kml"):
                return os.path.join(root, file)

    raise FileNotFoundError(f"No se encontró KML dentro de {kmz_path}")


def convertir_kmz(kmz_path: str, geojson_path: str):
    kml_path = extraer_kml_desde_kmz(kmz_path)
    gdf = gpd.read_file(kml_path)

    if gdf.empty:
        print(f"[AVISO] {kmz_path} no tiene geometrías")
        return

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326, allow_override=True)
    else:
        gdf = gdf.to_crs(epsg=4326)

    gdf.to_file(geojson_path, driver="GeoJSON")
    print(f"[OK] {kmz_path} -> {geojson_path}")


def main():
    os.makedirs(GEOJSON_FOLDER, exist_ok=True)

    archivos = [f for f in os.listdir(KMZ_FOLDER) if f.lower().endswith(".kmz")]
    archivos.sort()

    if not archivos:
        print("No se encontraron archivos KMZ en la carpeta kmz/")
        return

    for nombre in archivos:
        kmz_path = os.path.join(KMZ_FOLDER, nombre)
        salida = Path(nombre).stem + ".geojson"
        geojson_path = os.path.join(GEOJSON_FOLDER, salida)
        convertir_kmz(kmz_path, geojson_path)


if __name__ == "__main__":
    main()