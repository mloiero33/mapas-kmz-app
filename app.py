import json
import os

import folium
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Visor de mapas",
    layout="wide",
)

GEOJSON_FOLDER = "geojson"


@st.cache_data
def listar_geojson(carpeta):
    archivos = [f for f in os.listdir(
        carpeta) if f.lower().endswith(".geojson")]
    archivos.sort()
    return archivos


@st.cache_data
def cargar_geojson(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def obtener_bounds(data):
    coords = []

    def recorrer(obj):
        if isinstance(obj, list):
            if (
                len(obj) >= 2
                and isinstance(obj[0], (int, float))
                and isinstance(obj[1], (int, float))
            ):
                coords.append((obj[1], obj[0]))  # lat, lon
            else:
                for item in obj:
                    recorrer(item)

    for feature in data.get("features", []):
        geometry = feature.get("geometry")
        if geometry and "coordinates" in geometry:
            recorrer(geometry["coordinates"])

    if not coords:
        return None

    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]

    return [[min(lats), min(lons)], [max(lats), max(lons)]]


def obtener_campos_popup(features, max_campos=12):
    if not features:
        return []

    props = features[0].get("properties", {})
    # Tomamos todas las claves no vacías
    campos = [k for k in props.keys() if k]
    return campos[:max_campos]


def estilo_geojson(feature):
    geometry = feature.get("geometry", {})
    geom_type = geometry.get("type", "")

    if geom_type in ["LineString", "MultiLineString"]:
        return {
            "color": "#ff0000",
            "weight": 8,
            "opacity": 1,
        }

    return {
        "fillColor": "#ff0000",
        "color": "#000000",
        "weight": 6,
        "fillOpacity": 0.80,
    }


st.title("Visor de mapas")
st.caption("Abrí tus mapas desde celular o PC")

if not os.path.exists(GEOJSON_FOLDER):
    st.error("No existe la carpeta 'geojson'")
    st.stop()

archivos = listar_geojson(GEOJSON_FOLDER)

if not archivos:
    st.warning("No se encontraron archivos .geojson")
    st.stop()

archivo = st.selectbox("Elegí un mapa", archivos)

ruta = os.path.join(GEOJSON_FOLDER, archivo)
data = cargar_geojson(ruta)
features = data.get("features", [])

if not features:
    st.warning("Este archivo no contiene geometrías visibles.")
    st.stop()

campos = obtener_campos_popup(features)

m = folium.Map(
    control_scale=True,
    tiles="OpenStreetMap",
)

folium.GeoJson(
    data,
    name=archivo,
    style_function=estilo_geojson,
    highlight_function=lambda x: {
        "weight": 8,
        "fillOpacity": 0.95,
        "color": "#ffffff",
    },
    tooltip=folium.GeoJsonTooltip(
        fields=campos,
        aliases=[f"{c}:" for c in campos],
        localize=True,
        sticky=True,
        labels=True,
    ) if campos else None,
    popup=folium.GeoJsonPopup(
        fields=campos,
        aliases=[f"{c}:" for c in campos],
        localize=True,
        labels=True,
        style="""
            background-color: white;
            border: 2px solid #333333;
            border-radius: 8px;
            box-shadow: 3px;
        """,
    ) if campos else None,
).add_to(m)

bounds = obtener_bounds(data)
if bounds:
    m.fit_bounds(bounds)

folium.LayerControl().add_to(m)

st_folium(
    m,
    width=None,
    height=650,
    returned_objects=[],
    use_container_width=True,
)
