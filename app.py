import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(
    page_title="Portal de Vecinos - C.R. Villa Icabaru",
    page_icon="🏢",
    layout="wide"
)

# Coloca aquí tu ID de Google Sheet real
GOOGLE_SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg"

# 2. Estilos CSS Globales inyectados en la cabecera
st.markdown("""
    <style>
    .tarjeta-vecino {
        background-color: #ffffff !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
        border-left: 5px solid #1e293b !important;
        color: #1e293b !important;
    }
    .badge-unidad {
        background-color: #dbeafe !important;
        color: #1e40af !important;
        font-weight: bold !important;
        padding: 4px 10px !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        display: inline-block !important;
    }
    .vehiculo-block {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 4px !important;
        padding: 6px !important;
        font-family: monospace !important;
        margin-top: 4px !important;
        font-size: 13px !important;
        color: #334155 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Función inteligente para normalizar y mapear columnas borrosas
@st.cache_data(ttl=15)
def cargar_datos_desde_sheets():
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"
    try:
        df = pd.read_csv(url)
        # Reemplazar valores nulos por texto vacío inmediatamente
        df = df.fillna("")
        
        # Mapeo inteligente de columnas por aproximación de nombres
        mapeo_columnas = {}
        for col in df.columns:
            col_lower = col.strip().lower()
            if "uni" in col_lower: mapeo_columnas[col] = "unidad"
            elif "prop" in col_lower: mapeo_columnas[col] = "propietario"
            elif "inq" in col_lower: mapeo_columnas[col] = "inquilino"
            elif "tel" in col_lower and "eme" not in col_lower: mapeo_columnas[col] = "telefono"
            elif "plac1" in col_lower or "placa 1" in col_lower: mapeo_columnas[col] = "placa1"
            elif "vehi1" in col_lower or "vehiculo 1" in col_lower: mapeo_columnas[col] = "vehiculo1"
            elif "colo1" in col_lower or "color 1" in col_lower: mapeo_columnas[col] = "color1"
            elif "plac2" in col_lower or "placa 2" in col_lower: mapeo_columnas[col] = "placa2"
            elif "vehi2" in col_lower or "vehiculo 2" in col_lower: mapeo_columnas[col] = "vehiculo2"
            elif "colo2" in col_lower or "color 2" in col_lower: mapeo_columnas[col] = "color2"
            elif "eme" in col_lower and "tel" not in col_lower: mapeo_columnas[col] = "emergencia"
            elif "teleme" in col_lower or "tel_eme" in col_lower or "tel. eme" in col_lower: mapeo_columnas[col] = "telemergencia"
            elif "masc" in col_lower: mapeo_columnas[col] = "mascotas"
            elif "tipo" in col_lower and "masc" in col_lower: mapeo_columnas[col] = "tipomascotas"

        # Renombrar las columnas encontradas
        df = df.rename(columns=mapeo_columnas)
        
        # Si no se detectó columna 'unidad', usar la primera columna disponible como fallback
        if "unidad" not in df.columns and len(df.columns) > 0:
            df = df.rename(columns={df.columns[0]: "unidad"})

        # Limpieza estricta de filas vacías reales
        df['unidad_clean'] = df['unidad'].astype(str).str.strip()
        df = df[df['unidad_clean'] != ""]
        df = df[df['unidad_clean'].lower() != "nan"]
        
        # Si el propietario y el teléfono también están vacíos, es una fila fantasma
        if "propietario" in df.columns:
            df = df[(df['unidad_clean'] != "") | (df['propietario'].astype(str).str.strip() != "")]

        return df.to_dict(orient="records")
    except Exception as e:
        st.error(f"❌ Error crítico leyendo Google Sheets: {e}")
        return []

# Carga de la lista real de vecinos
vecinos = cargar_datos_desde_sheets()

# 4. Encabezado de la Aplicación
st.title("🏢 C.R. Villa Icabaru")
st.caption("Base de datos en tiempo real conectada a Google Sheets")
st.markdown("---")

if vecinos:
    # 5. Control de estado para las Torres
    if 'torre_seleccionada' not in st.session_state:
        st.session_state.torre_seleccionada = "Todas"

    # 6. Buscador
    busqueda = st.text_input(
        "🔍 Buscar Residente:",
        placeholder="Buscar por Apartamento, Residente, Placa o Vehículo..."
    ).strip().lower()

    # 7. Botones de Torres
    st.write("**Filtrar por Torre:**")
    cols_botones = st.columns(6)
    torres_opciones = ["Todas", "T1", "T2", "T3", "T4", "T5"]

    for i, torre in enumerate(torres_opciones):
        with cols_botones[i]:
            tipo_boton = "primary" if st.session_state.torre_seleccionada == torre else "secondary"
            nombre_mostrar_btn = "Todas" if torre == "Todas" else f"Torre {torre[-1]}"
            if st.button(nombre_mostrar_btn, type=tipo_boton, use_container_width=True, key=f"btn_{torre}"):
                st.session_state.torre_seleccionada = torre
                st.rerun()

    # 8. Filtrado de registros en memoria
    vecinos_filtrados = []
    for v in vecinos:
        unidad_txt = str(v.get("unidad", "")).strip().upper()
        
        if st.session_state.torre_seleccionada != "Todas" and not unidad_txt.startswith(st.session_state.torre_seleccionada):
            continue
            
        if busqueda:
            valores_registro = " ".join([str(val) for val in v.values()]).lower()
            if busqueda not in valores_registro:
                continue
                
        vecinos_filtrados.append(v)

    st.markdown(f"**Resultados encontrados:** {len(vecinos_filtrados)} unidades.")

    # 9. Despliegue en Grid con componentes nativos parciales para asegurar estabilidad
    if len(vecinos_filtrados) == 0:
        st.info("📭 No se encontraron registros con los criterios seleccionados.")
    else:
        grid = st.columns(2)
        for index, v in enumerate(vecinos_filtrados):
            with grid[index % 2]:
                
                # Extracción segura de datos mapeados
                unidad = str(v.get("unidad", "N/R")).strip()
                propietario = str(v.get("propietario", "")).strip()
                inquilino = str(v.get("inquilino", "")).strip()
                telefono = str(v.get("telefono", "")).strip()
                if not telefono: telefono = "Sin número"
                
                if inquilino and inquilino != "":
                    nombre_titular = inquilino
                    sublinea = f"👤 Inquilino (Prop: {propietario if propietario else 'N/R'})"
                else:
                    nombre_titular = propietario if propietario else "Nombre no registrado"
                    sublinea = "👤 Propietario Residente"
                
                # Co-residentes dinámicos
                coresidentes_lista = [str(v[col]).strip() for col in ["residente2", "residente3", "residente4", "residente5", "residente6"] if col in v and str(v[col]).strip() != ""]
                coresidentes_txt = ", ".join(coresidentes_lista)
                coresidentes_html = f"<p style='margin: 4px 0; font-size: 13px; color: #475569;'>👨‍👩‍👧‍👦 <b>Co-residentes:</b> {coresidentes_txt}</p>" if list(coresidentes_txt) else ""
                
                # Mascotas
                mascotas = str(v.get("mascotas", "")).strip()
                tipo_mascotas = str(v.get("tipomascotas", "")).strip()
                mascota_html = ""
                if mascotas and mascotas.lower() != "ninguna" and mascotas.lower() != "none":
                    detalle = f"{mascotas} ({tipo_mascotas})" if tipo_mascotas else mascotas
                    mascota_html = f"<p style='margin: 4px 0; font-size: 13px; color: #059669;'>🐾 <b>Mascota:</b> {detalle}</p>"

                # Vehículos
                vehiculos_disponibles = []
                for num in ["1", "2"]:
                    placa = str(v.get(f"placa{num}", "")).strip()
                    veh = str(v.get(f"vehiculo{num}", "")).strip()
                    col = str(v.get(f"color{num}", "")).strip()
                    if placa and placa.lower() != "nan":
                        vehiculos_disponibles.append(f"🚗 <b>{placa.upper()}</b> - {veh} ({col})")
                
                if vehiculos_disponibles:
                    vehiculos_html = "".join([f"<div class='vehiculo-block'>{p}</div>" for p in vehiculos_disponibles])
                else:
                    vehiculos_html = "<div class='vehiculo-block' style='color: #94a3b8;'>❌ Sin vehículos registrados</div>"

                # Emergencias
                emergencia = str(v.get("emergencia", "")).strip()
                tel_emergencia = str(v.get("telemergencia", "")).strip()
                if not emergencia or emergencia.lower() == "nan": emergencia = "No registrado"
                contacto_emergencia = f"{emergencia} (📞 {tel_emergencia})" if (tel_emergencia and tel_emergencia.lower() != "nan") else emergencia

                # Renderizado final encapsulado dentro de un contenedor seguro st.container
                with st.container():
                    html_tarjeta = f"""
                    <div class="tarjeta-vecino">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="badge-unidad">{unidad}</span>
                            <span style="font-size: 12px; color: #64748b; font-style: italic;">{sublinea}</span>
                        </div>
                        <h3 style="margin: 2px 0; color: #1e293b; font-size: 19px; font-weight: bold;">{nombre_titular}</h3>
                        <p style="margin: 2px 0; font-size: 14px; color: #1e293b;"><b>📞 Tel Principal:</b> <span style="color: #2563eb; font-weight: bold;">{telefono}</span></p>
                        {coresidentes_html}
                        {mascota_html}
                        <div style="margin-top: 10px;">
                            <span style="font-size: 11px; color: #64748b; font-weight: bold; text-transform: uppercase;">🔒 Vehículos Autorizados:</span>
                            {vehiculos_html}
                        </div>
                        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #475569;">
                            🚨 <b>Contacto de Emergencia:</b> <br>
                            <span style="color: #dc2626; font-weight: 500;">{contacto_emergencia}</span>
                        </div>
                    </div>
                    """
                    st.markdown(html_tarjeta, unsafe_allow_html=True)
else:
    st.warning("⚠️ La base de datos se leyó vacía. Asegúrate de colocar tu GOOGLE_SHEET_ID correcto.")
