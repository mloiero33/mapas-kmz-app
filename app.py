import json
import os

import folium
import streamlit as st
from streamlit_folium import st_folium
from folium.features import DivIcon
from folium import Marker


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


def agregar_marcadores_con_numeros(mapa, data, campo_nombre="Name"):
    """
    Agrega marcadores circulares con números para cada punto en el GeoJSON
    """
    features = data.get("features", [])
    
    for i, feature in enumerate(features, 1):
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        
        if geometry.get("type") in ["Point", "MultiPoint"]:
            coords = geometry.get("coordinates")
            
            # Obtener el nombre del punto
            nombre_punto = properties.get(campo_nombre, f"Punto {i}")
            
            # Si es MultiPoint, procesar cada punto
            if geometry.get("type") == "MultiPoint":
                for punto in coords:
                    crear_marcador(mapa, punto, nombre_punto)
            else:
                crear_marcador(mapa, coords, nombre_punto)


def crear_marcador(mapa, coords, texto):
    """
    Crea un marcador circular con texto
    """
    # Invertir coordenadas de [lon, lat] a [lat, lon] para folium
    lat, lon = coords[1], coords[0]
    
    # Limitar el texto a 3 caracteres para que entre en el círculo
    texto_corto = str(texto)[:3] if len(str(texto)) > 3 else str(texto)
    
    # Crear un marcador personalizado con número
    Marker(
        location=[lat, lon],
        icon=DivIcon(
            icon_size=(30, 30),
            icon_anchor=(15, 15),
            html=f'''
                <div style="
                    background-color: #ff4d4d;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                    cursor: pointer;
                ">
                    {texto_corto}
                </div>
            '''
        ),
        popup=texto,
        tooltip=texto
    ).add_to(mapa)


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

# Agregar las geometrías (líneas, polígonos)
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

# Agregar marcadores con números para los puntos (checkpoints)
agregar_marcadores_con_numeros(m, data, campo_nombre="Name")

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