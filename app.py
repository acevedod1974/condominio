import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(
    page_title="Portal de Vecinos - C.R. Villa Icabaru",
    page_icon="🏢",
    layout="wide"
)

# ID Real de tu Google Sheet
GOOGLE_SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg"

# 2. Estilos CSS Globales inyectados de forma segura
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
        font-family: Arial, sans-serif !important;
        margin-top: 6px !important;
        font-size: 13px !important;
        color: #334155 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Función Extractor Estricto por nombre de columna
@st.cache_data(ttl=10)
def cargar_datos_desde_sheets():
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"
    try:
        df = pd.read_csv(url)
        df = df.fillna("") # Rellenar nulos de forma global
        
        lista_vecinos = []
        
        for _, fila in df.iterrows():
            v_datos = {}
            
            # Mapeo por etiquetas literales
            v_datos["unidad"] = str(fila.get("Número de Unidad / Apartamento", "")).strip()
            v_datos["tipo_residente"] = str(fila.get("Tipo de Residente", "")).strip()
            
            # Datos Propietario
            v_datos["propietario"] = str(fila.get("Nombre Completo del Propietario", "")).strip()
            v_datos["tel_prop"] = str(fila.get("Número de Teléfono Celular Propietario", "")).strip()
            
            # Datos Inquilino
            v_datos["inquilino"] = str(fila.get("Nombre Completo del Inquilino / Residente", "")).strip()
            v_datos["tel_inq"] = str(fila.get("Número de Teléfono Celular Inquilino / Residente", "")).strip()
            
            # Mascotas
            v_datos["mascotas"] = str(fila.get("¿ Residen mascotas en el Apartamento?", "")).strip()
            v_datos["tipomascotas"] = str(fila.get("Tipos de Mascotas (Marque todas las que apliquen)", "")).strip()
            
            # Vehículo 1
            v_datos["placa1"] = str(fila.get("Placa del Vehiculo 1", "")).strip()
            v_datos["vehiculo1"] = str(fila.get("Marca / Modelo del Vehiculo 1", "")).strip()
            v_datos["color1"] = str(fila.get("Color del Vehiculo 1", "")).strip()
            
            # Vehículo 2
            v_datos["placa2"] = str(fila.get("Placa del Vehiculo 2", "")).strip()
            v_datos["vehiculo2"] = str(fila.get("Marca / Modelo del Vehiculo 2", "")).strip()
            v_datos["color2"] = str(fila.get("Color del Vehiculo 2", "")).strip()
            
            # Emergencias
            v_datos["emergencia"] = str(fila.get("En caso de emergencia (médica, incendio, fuga, etc.), ¿a quién debemos contactar si no logramos comunicarnos con el titular?", "")).strip()
            v_datos["telemergencia"] = str(fila.get("Número de Teléfono de Contacto de Emergencia", "")).strip()
            
            # Limpieza exhaustiva de textos basura flotantes (.0 de números telefónicos)
            for k in ["tel_prop", "tel_inq", "telemergencia"]:
                if v_datos[k].endswith(".0"):
                    v_datos[k] = v_datos[k][:-2]
            
            if v_datos["unidad"] and v_datos["unidad"].lower() != "nan" and v_datos["unidad"] != "":
                lista_vecinos.append(v_datos)
                
        return lista_vecinos
    except Exception as e:
        st.error(f"❌ Error leyendo Google Sheets: {e}")
        return []

# Cargar base de datos limpia
vecinos = cargar_datos_desde_sheets()

# 4. Títulos principales
st.title("🏢 Portal de Vecinos - C.R. Villa Icabaru")
st.caption("Control de Acceso y Datos de Residentes en Tiempo Real")
st.markdown("---")

if vecinos:
    if 'torre_seleccionada' not in st.session_state:
        st.session_state.torre_seleccionada = "Todas"

    # Buscador global inteligente
    busqueda = st.text_input(
        "🔍 Buscar Residente:",
        placeholder="Escribe apartamento (ej: T1 P2), nombre, apellido, placa..."
    ).strip().lower()

    # Botones de Filtrado por Torres
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

    # Filtros analíticos
    vecinos_filtrados = []
    for v in vecinos:
        unidad_txt = v["unidad"].upper()
        
        if st.session_state.torre_seleccionada != "Todas" and not unidad_txt.startswith(st.session_state.torre_seleccionada):
            continue
            
        if busqueda:
            valores_completos = " ".join([str(val) for val in v.values()]).lower()
            if busqueda not in valores_completos:
                continue
                
        vecinos_filtrados.append(v)

    st.markdown(f"**Resultados encontrados:** {len(vecinos_filtrados)} unidades.")

    if len(vecinos_filtrados) == 0:
        st.info("📭 No se encontraron registros con esos criterios.")
    else:
        # Renderizado en Grid de dos columnas
        grid = st.columns(2)
        for index, v in enumerate(vecinos_filtrados):
            with grid[index % 2]:
                
                unidad = v["unidad"]
                propietario = v["propietario"]
                inquilino = v["inquilino"]
                
                # Definición estricta de Titular y Número Celular
                if inquilino and inquilino != "" and inquilino.lower() != "nan":
                    nombre_titular = inquilino
                    telefono = v["tel_inq"] if v["tel_inq"] and v["tel_inq"].lower() != "nan" else "Sin número"
                    sublinea = f"👤 Inquilino / Arrendatario (Propietario: {propietario})"
                else:
                    nombre_titular = propietario if propietario else "No registrado"
                    telefono = v["tel_prop"] if v["tel_prop"] and v["tel_prop"].lower() != "nan" else "Sin número"
                    sublinea = "👤 Propietario Residente"

                # --- SANITIZACIÓN DEL BLOQUE MASCOTAS ---
                mascotas_check = v["mascotas"].lower().strip()
                mascota_html = ""
                if mascotas_check and mascotas_check not in ["ninguna", "none", "nan", "0", "no", ""]:
                    detalle_m = f"{v['mascotas']}"
                    if v["tipomascotas"] and v["tipomascotas"].lower() != "nan" and v["tipomascotas"] != "":
                        sub_detalle = v["tipomascotas"].replace("perro_m", "Perro Mediano").replace("perro_p", "Perro Pequeño").replace("perro_g", "Perro Grande").replace("gato", "Gato").replace("ave", "Ave").replace("otro_m", "Otro")
                        detalle_m += f" ({sub_detalle})"
                    mascota_html = f"<p style='margin: 4px 0; font-size: 14px; color: #059669;'>🐾 <b>Mascota:</b> {detalle_m}</p>"

                # --- PARSEO ULTRA SEGURO DE VEHÍCULOS (Arregla el fallo de lecturas) ---
                vehiculos_disponibles = []
                for num in ["1", "2"]:
                    placa_raw = str(v[f"placa{num}"]).strip()
                    veh_raw = str(v[f"vehiculo{num}"]).strip()
                    col_raw = str(v[f"color{num}"]).strip()
                    
                    # Evitar que 'nan', vacíos o textos por defecto se asuman como vehículos válidos
                    if placa_raw and placa_raw.lower() != "nan" and placa_raw != "" and "sin vehículos" not in placa_raw.lower():
                        datos_v = f"🚗 <b>{placa_raw.upper()}</b>"
                        if veh_raw and veh_raw.lower() != "nan" and veh_raw != "": 
                            datos_v += f" - {veh_raw}"
                        if col_raw and col_raw.lower() != "nan" and col_raw != "": 
                            datos_v += f" ({col_raw})"
                        vehiculos_disponibles.append(datos_v)
                
                # Renderizar la lista de vehículos en bloques HTML limpios sin saltos extraños
                if len(vehiculos_disponibles) > 0:
                    vehiculos_html = ""
                    for item in vehiculos_disponibles:
                        vehiculos_html += f"<div class='vehiculo-block'>{item}</div>"
                else:
                    vehiculos_html = "<div class='vehiculo-block' style='color: #94a3b8;'>❌ Sin vehículos registrados</div>"

                # --- SANITIZACIÓN DE CONTACTO DE EMERGENCIAS ---
                emergencia = v["emergencia"]
                tel_emergencia = v["telemergencia"]
                if not emergencia or emergencia.lower() == "nan" or emergencia == "": 
                    emergencia = "No registrado"
                contacto_emergencia = f"{emergencia} (📞 {tel_emergencia})" if tel_emergencia and tel_emergencia.lower() != "nan" and tel_emergencia != "" else emergencia

                # --- COMPILACIÓN FINAL UNIFICADA (Sin saltos de línea crudos dentro del f-string) ---
                html_tarjeta = f"""<div class="tarjeta-vecino"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;"><span class="badge-unidad">{unidad}</span><span style="font-size: 12px; color: #64748b; font-style: italic;">{sublinea}</span></div><h3 style="margin: 2px 0; color: #1e293b; font-size: 19px; font-weight: bold;">{nombre_titular}</h3><p style="margin: 4px 0; font-size: 14px; color: #1e293b;"><b>📞 Teléfono Celular:</b> <span style="color: #2563eb; font-weight: bold;">{telefono}</span></p>{mascota_html}<div style="margin-top: 10px;"><span style="font-size: 11px; color: #64748b; font-weight: bold; text-transform: uppercase;">🔒 Vehículos Autorizados:</span>{vehiculos_html}</div><div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #475569;">🚨 <b>Contacto de Emergencia:</b> <br><span style="color: #dc2626; font-weight: 500;">{contacto_emergencia}</span></div></div>"""
                
                st.markdown(html_tarjeta, unsafe_allow_html=True)
else:
    st.warning("⚠️ Error al sincronizar con el formulario. Verifica que el enlace de Google Sheets esté configurado como público.")
