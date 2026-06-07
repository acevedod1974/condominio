import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(
    page_title="C.R. Villa Icabaru - Portal de Vecinos",
    page_icon="🏢",
    layout="wide"
)

# REEMPLAZA ESTA ID por la ID real de tu Google Sheet
# La encuentras en la URL de tu navegador: https://docs.google.com/spreadsheets/d/AQUÍ_ESTÁ_LA_ID/edit
GOOGLE_SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg"

# 2. Inyección de estilos CSS para las tarjetas
st.markdown("""
    <style>
    .tarjeta-vecino {
        background-color: #ffffff;
        padding: 16px;
        margin-bottom: 12px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid #1e293b;
    }
    .badge-unidad {
        background-color: #dbeafe;
        color: #1e40af;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 4px;
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
    }
    </style>
""", unsafe_allow_html=True)

# 3. Función para leer el Google Sheet en tiempo real
@st.cache_data(ttl=60) # Actualiza los datos cada 60 segundos si hay cambios en el Sheet
def cargar_datos_desde_sheets():
    # Construye la URL de exportación en formato CSV
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"
    
    try:
        df = pd.read_csv(url)
        # Limpiamos los nombres de las columnas (quitamos espacios y pasamos a minúsculas)
        df.columns = df.columns.str.strip().str.lower()
        
        # Convertimos el DataFrame a una lista de diccionarios (JSON-like)
        # Reemplazamos valores NaN (vacíos) por None o texto limpio
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {e}")
        st.info("Asegúrate de que el enlace de tu Google Sheet esté configurado como 'Cualquier persona con el enlace puede ver'.")
        return []

# Llamada a la función de carga real
vecinos = cargar_datos_desde_sheets()

# 4. Encabezado de la aplicación
st.title("🏢 C.R. Villa Icabaru")
st.caption("Base de datos en tiempo real conectada a Google Sheets")
st.markdown("---")

if vecinos:
    # 5. Inicializar el estado de la Torre Seleccionada
    if 'torre_seleccionada' not in st.session_state:
        st.session_state.torre_seleccionada = "Todas"

    # 6. Barra de Búsqueda de texto
    busqueda = st.text_input(
        "🔍 Buscar Residente:",
        placeholder="Buscar por Apartamento, Residente, Placa, Marca o Modelo de Vehículo..."
    ).strip().lower()

    # 7. Fila de Botones para filtrar por Torre
    st.write("**Filtrar por Torre:**")
    cols_botones = st.columns(6)
    torres_opciones = ["Todas", "T1", "T2", "T3", "T4", "T5"]

    for i, torre in enumerate(torres_opciones):
        with cols_botones[i]:
            tipo_boton = "primary" if st.session_state.torre_seleccionada == torre else "secondary"
            if st.button(f"Torre {torre[-1]}" if torre != "Todas" else "Todas", type=tipo_boton, use_container_width=True):
                st.session_state.torre_seleccionada = torre
                st.rerun()

    # 8. Lógica de Filtrado combinada
    vecinos_filtrados = []
    for v in vecinos:
        # Asegurar que el campo unidad exista en tu excel/sheet
        unidad_texto = str(v.get("unidad", "")).strip()
        
        # Filtro de botón de torre
        if st.session_state.torre_seleccionada != "Todas" and not unidad_texto.upper().startswith(st.session_state.torre_seleccionada):
            continue
            
        # Filtro de cuadro de búsqueda de texto
        if busqueda:
            # Reúne todos los valores de las columnas en una sola cadena para buscar en todo el registro
            valores_registro = " ".join([str(val) for val in v.values()]).lower()
            if busqueda not in valores_registro:
                continue
                
        vecinos_filtrados.append(v)

    # 9. Mostrar Contador de Resultados
    st.markdown(f"**Resultados encontrados:** {len(vecinos_filtrados)} unidades.")

    # 10. Despliegue de Tarjetas dinámicas basadas en las columnas de TU Sheet
    if len(vecinos_filtrados) == 0:
        st.info("📭 No se encontraron resultados que coincidan con los criterios de búsqueda.")
    else:
        grid = st.columns(2)
        for index, v in enumerate(vecinos_filtrados):
            with grid[index % 2]:
                # Mapeo dinámico y tolerante basado en las columnas que nos mostraste en Apps Script:
                unidad = v.get("unidad", "N/R")
                propietario = v.get("propietario", "Nombre no registrado")
                inquilino = v.get("inquilino", "")
                telefono = v.get("telefono", "Sin número")
                
                # Identificar el nombre a mostrar prioritario
                nombre_titular = inquilino if (inquilino and str(inquilino).strip() != "") else propietario
                sublinea = f"👤 Inquilino (Propietario: {propietario})" if (inquilino and str(inquilino).strip() != "") else "👤 Propietario Residente"
                
                # Co-residentes (Busca si tienes las columnas 'residente2', etc, o una columna general 'coresidentes')
                coresidentes_lista = [str(v[col]) for col in ["residente2", "residente3", "residente4", "residente5", "residente6"] if col in v and str(v[col]).strip() != ""]
                if not coresidentes_lista and "coresidentes" in v:
                    coresidentes_txt = str(v["coresidentes"])
                else:
                    coresidentes_txt = ", ".join(coresidentes_lista)
                
                coresidentes_html = f"<p style='margin: 4px 0; font-size: 13px; color: #475569;'>👨‍👩‍👧‍👦 <b>Co-residentes:</b> {coresidentes_txt}</p>" if coresidentes_txt else ""
                
                # Mascotas
                mascotas = v.get("mascotas", "")
                tipo_mascotas = v.get("tipomascotas", "")
                mascota_html = ""
                if mascotas and str(mascotas).lower() != "ninguna" and str(mascotas).lower() != "none":
                    mascota_html = f"<p style='margin: 4px 0; font-size: 13px; color: #059669;'>🐾 <b>Mascota:</b> {mascotas} ({tipo_mascotas})</p>"

                # Vehículos (Detecta columnas placa1, placa2, etc.)
                vehiculos_disponibles = []
                for num in ["1", "2", "3"]:
                    placa_col = f"placa{num}"
                    veh_col = f"vehiculo{num}"
                    color_col = f"color{num}"
                    if placa_col in v and str(v[placa_col]).strip() != "":
                        vehiculos_disponibles.append(f"🚗 <b>{str(v[placa_col]).upper()}</b> - {v.get(veh_col, '')} ({v.get(color_col, '')})")
                
                if vehiculos_disponibles:
                    vehiculos_html = "".join([f"<div class='vehiculo-block'>{p}</div>" for p in vehiculos_disponibles])
                else:
                    vehiculos_html = "<div class='vehiculo-block' style='color: #94a3b8;'>❌ Sin vehículos registrados</div>"

                # Emergencia
                emergencia = v.get("emergencia", "No registrado")
                tel_emergencia = v.get("telemergencia", "")
                contacto_emergencia = f"{emergencia} (📞 {tel_emergencia})" if tel_emergencia else emergencia

                # Construcción final de la tarjeta HTML limpia
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
                        <span style="font-size: 12px; color: #64748b; font-weight: bold;">🔒 VEHÍCULOS AUTORIZADOS:</span>
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
    st.warning("⚠️ Esperando inicialización correcta de datos desde el Google Sheet.")