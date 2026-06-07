import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(
    page_title="Portal de Vecinos - C.R. Villa Icabaru",
    page_icon="🏢",
    layout="wide"
)

# Tu ID de Google Sheet Real
GOOGLE_SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg"

# 2. Estilos CSS Globales
st.markdown("""
    <style>
    .tarjeta-vecino {
        background-color: #ffffff !important;
        padding: 18px !important;
        margin-bottom: 16px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        border-left: 6px solid #1e293b !important;
        color: #1e293b !important;
    }
    .badge-unidad {
        background-color: #dbeafe !important;
        color: #1e40af !important;
        font-weight: bold !important;
        padding: 4px 12px !important;
        border-radius: 6px !important;
        font-size: 14px !important;
        display: inline-block !important;
    }
    .vehiculo-block {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        padding: 8px !important;
        font-family: monospace !important;
        margin-top: 6px !important;
        font-size: 13px !important;
        color: #334155 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Función Segura para procesar la estructura exacta del formulario
@st.cache_data(ttl=10)
def cargar_datos_desde_sheets():
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"
    try:
        df = pd.read_csv(url)
        
        # Limpieza inicial de nombres de columnas originales
        columnas_originales = [str(c).strip() for c in df.columns]
        
        lista_vecinos = []
        
        # Iteramos fila por fila usando los índices de posición física de las columnas
        # Esto evita por completo el error de nombres duplicados o "Name: 0, dtype: object"
        for _, fila in df.iterrows():
            # Creamos un diccionario limpio para cada vecino
            v_datos = {}
            
            # Buscaremos los datos recorriendo las columnas originales de tu formulario
            for i, col_nombre in enumerate(columnas_originales):
                col_lower = col_nombre.lower()
                valor_celda = str(fila.iloc[i]).strip()
                if valor_celda.lower() == "nan" or valor_celda == "None":
                    valor_celda = ""
                
                # Asignación manual indexada por palabras clave unívocas
                if "nro de apartamento" in col_lower or "número de apartamento" in col_lower or "unidad" in col_lower or i == 1:
                    if not v_datos.get("unidad"): v_datos["unidad"] = valor_celda
                elif "propietario" in col_lower and "c.i" not in col_lower and "telé" not in col_lower and "correo" not in col_lower:
                    if not v_datos.get("propietario"): v_datos["propietario"] = valor_celda
                elif "inquilino" in col_lower and "c.i" not in col_lower and "telé" not in col_lower and "correo" not in col_lower:
                    if not v_datos.get("inquilino"): v_datos["inquilino"] = valor_celda
                elif "teléfono" in col_lower or "telefono" in col_lower:
                    # Guardamos el primer teléfono que encontremos como principal si no hay uno asignado
                    if not v_datos.get("telefono") and valor_celda: 
                        v_datos["telefono"] = valor_celda
                elif "mascota" in col_lower:
                    if "tipo" in col_lower:
                        v_datos["tipomascotas"] = valor_celda
                    else:
                        v_datos["mascotas"] = valor_celda
                elif "placa" in col_lower:
                    if "1" in col_lower or "primer" in col_lower: v_datos["placa1"] = valor_celda
                    elif "2" in col_lower or "segund" in col_lower: v_datos["placa2"] = valor_celda
                elif "vehículo" in col_lower or "vehiculo" in col_lower or "modelo" in col_lower:
                    if "1" in col_lower or "primer" in col_lower: v_datos["vehiculo1"] = valor_celda
                    elif "2" in col_lower or "segund" in col_lower: v_datos["vehiculo2"] = valor_celda
                elif "color" in col_lower:
                    if "1" in col_lower or "primer" in col_lower: v_datos["color1"] = valor_celda
                    elif "2" in col_lower or "segund" in col_lower: v_datos["color2"] = valor_celda
                elif "emergencia" in col_lower:
                    if "tel" in col_lower or "cel" in col_lower: v_datos["telemergencia"] = valor_celda
                    else: v_datos["emergencia"] = valor_celda

            # Validar que la unidad no esté vacía antes de agregar al vecino
            unidad_final = v_datos.get("unidad", "").strip()
            if unidad_final and unidad_final.lower() != "nan" and not unidad_final.startswith("unidad"):
                lista_vecinos.append(v_datos)
                
        return lista_vecinos
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets: {e}")
        return []

# Cargar base de datos procesada
vecinos = cargar_datos_desde_sheets()

# 4. Títulos de la App
st.title("🏢 Portal de Vecinos - C.R. Villa Icabaru")
st.caption("Control de Acceso y Datos de Residentes en Tiempo Real")
st.markdown("---")

if vecinos:
    # 5. Inicializar Estado de las Torres
    if 'torre_seleccionada' not in st.session_state:
        st.session_state.torre_seleccionada = "Todas"

    # 6. Buscador global
    busqueda = st.text_input(
        "🔍 Buscar Residente:",
        placeholder="Escribe el apartamento, nombre, apellido, placas..."
    ).strip().lower()

    # 7. Filtros por Torres (Botones)
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

    # 8. Filtrado en Memoria Inteligente
    vecinos_filtrados = []
    for v in vecinos:
        unidad_txt = str(v.get("unidad", "")).strip().upper()
        
        # Filtro de Torre
        if st.session_state.torre_seleccionada != "Todas" and not unidad_txt.startswith(st.session_state.torre_seleccionada):
            continue
            
        # Filtro de Texto
        if busqueda:
            valores_completos = " ".join([str(val) for val in v.values()]).lower()
            if busqueda not in valores_completos:
                continue
                
        vecinos_filtrados.append(v)

    st.markdown(f"**Resultados encontrados:** {len(vecinos_filtrados)} unidades.")

    # 9. Construcción del Grid de Tarjetas (2 Columnas)
    if len(vecinos_filtrados) == 0:
        st.info("📭 No se encontraron registros coincidentes.")
    else:
        grid = st.columns(2)
        for index, v in enumerate(vecinos_filtrados):
            with grid[index % 2]:
                
                # Datos Base
                unidad = str(v.get("unidad", "N/R")).strip()
                propietario = str(v.get("propietario", "")).strip()
                inquilino = str(v.get("inquilino", "")).strip()
                telefono = str(v.get("telefono", "Sin número")).strip()
                
                # Identificar quién vive (Inquilino vs Propietario)
                if inquilino and inquilino.lower() != "nan" and inquilino != "":
                    nombre_titular = inquilino
                    sublinea = f"👤 Inquilino (Propietario: {propietario if propietario else 'N/R'})"
                else:
                    nombre_titular = propietario if propietario else "Nombre no registrado"
                    sublinea = "👤 Propietario Residente"
                
                # Filtro de Mascotas limpio
                mascotas = str(v.get("mascotas", "")).strip()
                tipo_masc = str(v.get("tipomascotas", "")).strip()
                mascota_html = ""
                if mascotas and mascotas.lower() not in ["ninguna", "none", "nan", "no"]:
                    detalles_mascota = f"{mascotas} ({tipo_masc})" if tipo_masc else mascotas
                    mascota_html = f"<p style='margin: 4px 0; font-size: 13px; color: #059669;'>🐾 <b>Mascota:</b> {detalles_mascota}</p>"

                # Filtro de Vehículos Autorizados
                vehiculos_disponibles = []
                for num in ["1", "2"]:
                    placa = str(v.get(f"placa{num}", "")).strip()
                    veh = str(v.get(f"vehiculo{num}", "")).strip()
                    col = str(v.get(f"color{num}", "")).strip()
                    if placa and placa.lower() != "nan" and placa != "":
                        vehiculos_disponibles.append(f"🚗 <b>{placa.upper()}</b> - {veh} {f'({col})' if col else ''}")
                
                if vehiculos_disponibles:
                    vehiculos_html = "".join([f"<div class='vehiculo-block'>{p}</div>" for p in vehiculos_disponibles])
                else:
                    vehiculos_html = "<div class='vehiculo-block' style='color: #94a3b8;'>❌ Sin vehículos registrados</div>"

                # Contacto de Emergencia
                emergencia = str(v.get("emergencia", "")).strip()
                tel_emergencia = str(v.get("telemergencia", "")).strip()
                if not emergencia or emergencia.lower() == "nan": 
                    emergencia = "No registrado"
                contacto_emergencia = f"{emergencia} (📞 {tel_emergencia})" if tel_emergencia else emergencia

                # Maquetación HTML Limpia y Renderizada por Streamlit
                with st.container():
                    html_tarjeta = f"""
                    <div class="tarjeta-vecino">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="badge-unidad">{unidad}</span>
                            <span style="font-size: 12px; color: #64748b; font-style: italic;">{sublinea}</span>
                        </div>
                        <h3 style="margin: 2px 0; color: #1e293b; font-size: 19px; font-weight: bold;">{nombre_titular}</h3>
                        <p style="margin: 2px 0; font-size: 14px; color: #1e293b;"><b>📞 Teléfono:</b> <span style="color: #2563eb; font-weight: bold;">{telefono}</span></p>
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
    st.warning("⚠️ No se pudo procesar la información. Revisa que tu Google Sheet tenga las columnas de apartamentos y propietarios con texto válido.")
