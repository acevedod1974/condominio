import streamlit as st
import pandas as pd

# 1. Configuración de la página (Debe ser la primera instrucción)
st.set_page_config(
    page_title="Portal de Vecinos - C.R. Villa Icabaru",
    page_icon="🏢",
    layout="wide"
)

# REEMPLAZA ESTA ID POR LA DE TU HOJA REAL
GOOGLE_SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg"

# 2. Estilos CSS Globales inyectados de forma segura
st.markdown("""
    <style>
    .tarjeta-vecino {
        background-color: #ffffff;
        padding: 16px;
        margin-bottom: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        border-left: 5px solid #1e293b;
    }
    .badge-unidad {
        background-color: #dbeafe;
        color: #1e40af;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
    }
    .vehiculo-block {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 6px;
        font-family: monospace;
        margin-top: 4px;
        font-size: 13px;
        color: #334155;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Función optimizada para cargar datos reales
@st.cache_data(ttl=30)
def cargar_datos_desde_sheets():
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        
        # ELIMINAR FILAS VACÍAS: Si la columna 'unidad' o 'propietario' están vacías, descartamos la fila
        if 'unidad' in df.columns:
            df = df.dropna(subset=['unidad'])
            df = df[df['unidad'].astype(str).str.strip() != ""]
            
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {e}")
        return []

# Carga de la lista real de vecinos
vecinos = cargar_datos_desde_sheets()

# 4. Encabezado de la Aplicación
st.title("🏢 C.R. Villa Icabaru")
st.caption("Base de datos en tiempo real conectada a Google Sheets")
st.markdown("---")

if vecinos:
    # 5. Control de estado para los botones de las Torres
    if 'torre_seleccionada' not in st.session_state:
        st.session_state.torre_seleccionada = "Todas"

    # 6. Buscador inteligente en la parte superior
    busqueda = st.text_input(
        "🔍 Buscar Residente:",
        placeholder="Buscar por Apartamento, Residente, Placa, Marca o Modelo de Vehículo..."
    ).strip().lower()

    # 7. Distribución de los botones para las Torres
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

    # 8. Procesamiento del filtro en memoria
    vecinos_filtrados = []
    for v in vecinos:
        unidad_txt = str(v.get("unidad", "")).strip().upper()
        
        # Filtro 1: Botón de Torre
        if st.session_state.torre_seleccionada != "Todas" and not unidad_txt.startswith(st.session_state.torre_seleccionada):
            continue
            
        # Filtro 2: Cuadro de búsqueda de texto
        if busqueda:
            valores_registro = " ".join([str(val) for val in v.values()]).lower()
            if busqueda not in valores_registro:
                continue
                
        vecinos_filtrados.append(v)

    # 9. Contador Informativo
    st.markdown(f"**Resultados encontrados:** {len(vecinos_filtrados)} unidades.")

    # 10. Despliegue en Grid Estricto con HTML Activado
    if len(vecinos_filtrados) == 0:
        st.info("📭 No se encontraron resultados con los criterios seleccionados.")
    else:
        grid = st.columns(2)
        for index, v in enumerate(vecinos_filtrados):
            with grid[index % 2]:
                
                # Mapeo seguro de campos de la fila actual
                unidad = str(v.get("unidad", "N/R")).strip()
                propietario = str(v.get("propietario", "Nombre no registrado")).strip()
                inquilino = str(v.get("inquilino", "")).strip()
                telefono = str(v.get("telefono", "Sin número")).strip()
                
                # Gestión de nombres prioritarios
                if inquilino and inquilino != "":
                    nombre_titular = inquilino
                    sublinea = f"👤 Inquilino (Propietario: {propietario})"
                else:
                    nombre_titular = propietario if propietario else "Nombre no registrado"
                    sublinea = "👤 Propietario Residente"
                
                # Construcción de Co-residentes
                coresidentes_lista = [str(v[col]).strip() for col in ["residente2", "residente3", "residente4", "residente5", "residente6"] if col in v and str(v[col]).strip() != ""]
                coresidentes_txt = ", ".join(coresidentes_lista) if coresidentes_lista else str(v.get("coresidentes", ""))
                coresidentes_html = f"<p style='margin: 4px 0; font-size: 13px; color: #475569;'>👨‍👩‍👧‍👦 <b>Co-residentes:</b> {coresidentes_txt}</p>" if coresidentes_txt else ""
                
                # Gestión de Mascotas (CORREGIDO SIN EL OPERADOR WALRUS)
                mascotas = str(v.get("mascotas", "")).strip()
                tipo_mascotas = str(v.get("tipomascotas", "")).strip()
                mascota_html = ""
                if mascotas and mascotas.lower() != "ninguna" and mascotas.lower() != "none":
                    mascota_html = f"<p style='margin: 4px 0; font-size: 13px; color: #059669;'>🐾 <b>Mascota:</b> {mascotas} ({tipo_mascotas})</p>"

                # Gestión de Vehículos Múltiples
                vehiculos_disponibles = []
                for num in ["1", "2", "3"]:
                    placa = str(v.get(f"placa{num}", "")).strip()
                    veh = str(v.get(f"vehiculo{num}", "")).strip()
                    col = str(v.get(f"color{num}", "")).strip()
                    if placa:
                        vehiculos_disponibles.append(f"🚗 <b>{placa.upper()}</b> - {veh} ({col})")
                
                if vehiculos_disponibles:
                    vehiculos_html = "".join([f"<div class='vehiculo-block'>{p}</div>" for p in vehiculos_disponibles])
                else:
                    vehiculos_html = "<div class='vehiculo-block' style='color: #94a3b8;'>❌ Sin vehículos registrados</div>"

                # Datos de Contacto de Emergencia
                emergencia = str(v.get("emergencia", "No registrado")).strip()
                tel_emergencia = str(v.get("telemergencia", "")).strip()
                contacto_emergencia = f"{emergencia} (📞 {tel_emergencia})" if tel_emergencia else emergencia

                # Maquetación estructurada de la tarjeta en HTML limpio
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
    st.warning("⚠️ No se pudieron estructurar registros. Verifica los nombres de tus columnas en Google Sheets.")
