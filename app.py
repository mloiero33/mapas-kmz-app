import os
import tempfile
import zipfile

import folium
import geopandas as gpd
import streamlit as st
from streamlit_folium import st_folium


# =========================
# Configuración general
# =========================
st.set_page_config(
    page_title="Visor de mapas KMZ",
    layout="wide",
)

KMZ_FOLDER = "kmz"


# =========================
# Funciones auxiliares
# =========================
@st.cache_data
def listar_kmz(carpeta: str) -> list[str]:
    archivos = [
        f for f in os.listdir(carpeta)
        if f.lower().endswith(".kmz")
    ]
    archivos.sort()
    return archivos


@st.cache_data
def extraer_kml_desde_kmz(kmz_path: str) -> str:
    """
    Extrae temporalmente el contenido del KMZ y devuelve la ruta del primer KML encontrado.
    """
    temp_dir = tempfile.mkdtemp()

    with zipfile.ZipFile(kmz_path, "r") as z:
        z.extractall(temp_dir)

    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.lower().endswith(".kml"):
                return os.path.join(root, file)

    raise FileNotFoundError(
        "No se encontró ningún archivo KML dentro del KMZ.")


@st.cache_data
def leer_kmz(kmz_path: str) -> gpd.GeoDataFrame:
    """
    Lee un KMZ y devuelve un GeoDataFrame en EPSG:4326.
    """
    kml_path = extraer_kml_desde_kmz(kmz_path)
    gdf = gpd.read_file(kml_path)

    if gdf.empty:
        return gdf

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326, allow_override=True)
    else:
        gdf = gdf.to_crs(epsg=4326)

    return gdf


def obtener_centro(gdf: gpd.GeoDataFrame) -> tuple[float, float]:
    """
    Calcula el centro aproximado del GeoDataFrame.
    """
    minx, miny, maxx, maxy = gdf.total_bounds
    lat = (miny + maxy) / 2
    lon = (minx + maxx) / 2
    return lat, lon


def elegir_campos_mostrar(gdf: gpd.GeoDataFrame, max_campos: int = 5) -> list[str]:
    """
    Elige columnas útiles para tooltip/popup, excluyendo geometry.
    """
    columnas = [c for c in gdf.columns if c != "geometry"]
    return columnas[:max_campos]


def estilo_geojson(feature):
    return {
        "fillColor": "#F0070B",
        "color": "#B90606",
        "weight": 4,
        "fillOpacity": 0.40,
    }


# =========================
# Interfaz
# =========================
st.title("Visor de mapas KMZ")
st.caption("Abrí cualquiera de tus mapas desde el celular o la PC.")

if not os.path.exists(KMZ_FOLDER):
    st.error(f"No existe la carpeta '{KMZ_FOLDER}'.")
    st.stop()

archivos_kmz = listar_kmz(KMZ_FOLDER)

if not archivos_kmz:
    st.warning("No se encontraron archivos .kmz en la carpeta.")
    st.stop()

# Selector simple, ideal para celular
archivo_seleccionado = st.selectbox(
    "Elegí un mapa",
    archivos_kmz,
    index=0,
)

ruta_kmz = os.path.join(KMZ_FOLDER, archivo_seleccionado)

# Opciones simples
with st.expander("Opciones"):
    mostrar_tooltip = st.checkbox("Mostrar nombres al pasar/tocar", value=True)
    zoom_inicial = st.slider(
        "Zoom inicial", min_value=5, max_value=16, value=11)

# =========================
# Cargar mapa
# =========================
try:
    gdf = leer_kmz(ruta_kmz)

    if gdf.empty:
        st.warning("Este KMZ no contiene geometrías visibles.")
        st.stop()

    lat, lon = obtener_centro(gdf)
    campos = elegir_campos_mostrar(gdf, max_campos=8)

    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom_inicial,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    geojson_kwargs = {
        "data": gdf,
        "name": archivo_seleccionado,
        "style_function": estilo_geojson,
        "highlight_function": lambda x: {
            "weight": 4,
            "fillOpacity": 0.45,
        },
    }

    if mostrar_tooltip and campos:
        geojson_kwargs["tooltip"] = folium.GeoJsonTooltip(
            fields=campos,
            aliases=[f"{c}:" for c in campos],
            localize=True,
            sticky=False,
            labels=True,
        )

    if campos:
        geojson_kwargs["popup"] = folium.GeoJsonPopup(
            fields=campos,
            aliases=[f"{c}:" for c in campos],
            localize=True,
            labels=True,
        )

    folium.GeoJson(**geojson_kwargs).add_to(m)
    folium.LayerControl().add_to(m)

    st_folium(
        m,
        width=None,
        height=600,
        returned_objects=[],
        use_container_width=True,
    )

except Exception as e:
    st.error(f"No se pudo abrir el archivo '{archivo_seleccionado}'.")
    st.exception(e)
