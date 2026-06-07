exports.handler = async function (event, context) {
  const SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg";
  // Exportación directa asegurando codificación UTF-8 limpia
  const GOOGLE_CSV_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv&gid=0`;

  try {
    // 1. Intentar usar Netlify Blobs si está disponible nativamente
    let store = null;
    let cachedData = null;

    try {
      const { getStore } = require("@netlify/blobs");
      store = getStore({
        name: "censo_villa_icabaru",
        siteID: context.siteID,
        token:
          context.clientContext?.custom?.netlify ||
          process.env.NETLIFY_AUTH_TOKEN,
      });

      if (store) {
        cachedData = await store.get("lista_vecinos", { type: "json" });
        let metadata = (await store.get("metadata_cache", {
          type: "json",
        })) || { lastUpdated: 0 };
        const cincoMinutos = 5 * 60 * 1000;

        if (cachedData && Date.now() - metadata.lastUpdated < cincoMinutos) {
          return {
            statusCode: 200,
            headers: {
              "Content-Type": "application/json",
              "Access-Control-Allow-Origin": "*",
            },
            body: JSON.stringify({
              fuente: "netlify_blobs_cache",
              datos: cachedData,
            }),
          };
        }
      }
    } catch (e) {
      console.log(
        "Aviso: Modo Directo Activo (Saltando caché de Blobs):",
        e.message,
      );
    }

    // 2. Descarga directa desde Google Sheets (Failover)
    const response = await fetch(GOOGLE_CSV_URL);
    if (!response.ok)
      throw new Error(
        `Google Sheets respondió con estatus: ${response.status}`,
      );

    const csvTexto = await response.text();

    // Parseador robusto lineal compatible con saltos de línea e isolación de comillas
    const lineas = csvTexto.split(/\r?\n/);
    if (lineas.length < 2)
      throw new Error("El archivo CSV está vacío o corrupto");

    // Normalizar cabeceras removiendo comillas y espacios remanentes
    const cabeceras = lineas[0]
      .split(",")
      .map((h) => h.replace(/^"|"$/g, "").trim());

    // Mapeo basado exactamente en las etiquetas de los archivos survey.csv y choices.csv del XLSForm
    const mapaColumnas = {
      unidad: "numero_unidad",
      tipo_residente: "tipo_residente",
      propietario: "nombre_propietario",
      tel_prop: "telefono_propietario",
      inquilino: "nombre_inquilino",
      tel_inq: "telefono_inquilino",
      mascotas: "residen_mascotas",
      tipomascotas: "tipos_mascotas",
      placa1: "placa_vehiculo_1",
      vehiculo1: "marca_modelo_1",
      color1: "color_vehiculo_1",
      placa2: "placa_vehiculo_2",
      vehiculo2: "marca_modelo_2",
      color2: "color_vehiculo_2",
      placa3: "placa_vehiculo_3",
      vehiculo3: "marca_modelo_3",
      color3: "color_vehiculo_3",
      emergencia: "contacto_emergencia",
      telemergencia: "telefono_emergencia",
    };

    const indices = {};
    Object.keys(mapaColumnas).forEach((clave) => {
      indices[clave] = cabeceras.findIndex(
        (h) => h.toLowerCase() === mapaColumnas[clave].toLowerCase(),
      );
    });

    const listadoProcesado = [];
    const regexCSV = /(".*?"|[^",\s]+)(?=\s*,|\s*$)/g;

    for (let i = 1; i < lineas.length; i++) {
      const linea = lineas[i].trim();
      if (!linea) continue;

      // Dividir celdas respetando comas internas encerradas en comillas
      let celdas = linea.match(regexCSV) || linea.split(",");

      const extraer = (clave) => {
        const idx = indices[clave];
        if (idx === undefined || idx === -1 || idx >= celdas.length) return "";
        let texto = celdas[idx].replace(/^"|"$/g, "").trim();

        if (["tel_prop", "tel_inq", "telemergencia"].includes(clave)) {
          if (texto.endsWith(".0")) texto = texto.slice(0, -2);
          if (texto.toLowerCase() === "nan" || texto === "0") texto = "";
        }
        return texto;
      };

      const unidad = extraer("unidad");
      if (!unidad || unidad.toLowerCase() === "nan") continue;

      const registro = {
        unidad,
        tipo_residente: extraer("tipo_residente"),
        propietario: extraer("propietario"),
        tel_prop: extraer("tel_prop"),
        inquilino: extraer("inquilino"),
        tel_inq: extraer("tel_inq"),
        mascotas: extraer("mascotas"),
        tipomascotas: extraer("tipomascotas"),
        placa1: extraer("placa1"),
        vehiculo1: extraer("vehiculo1"),
        color1: extraer("color1"),
        placa2: extraer("placa2"),
        vehiculo2: extraer("vehiculo2"),
        color2: extraer("color2"),
        placa3: extraer("placa3"),
        vehiculo3: extraer("vehiculo3"),
        color3: extraer("color3"),
        emergencia: extraer("emergencia"),
        telemergencia: extraer("telemergencia"),
      };

      // Limpieza cosmética de etiquetas del formulario para el UI
      if (registro.tipo_residente === "propietario_residente")
        registro.tipo_residente = "Propietario Residente";
      if (registro.tipo_residente === "inquilino_arrendatario")
        registro.tipo_residente = "Inquilino / Arrendatario";

      // Índice unificado de coincidencia para búsquedas
      registro.search_index =
        `${registro.unidad} ${registro.propietario} ${registro.inquilino} ${registro.placa1} ${registro.placa2} ${registro.placa3} ${registro.vehiculo1} ${registro.vehiculo2} ${registro.vehiculo3}`.toLowerCase();

      listadoProcesado.push(registro);
    }

    // Guardar asíncronamente en caché si la tienda de Blobs está activa
    if (store && listadoProcesado.length > 0) {
      try {
        await store.set("lista_vecinos", JSON.stringify(listadoProcesado));
        await store.set(
          "metadata_cache",
          JSON.stringify({ lastUpdated: Date.now() }),
        );
      } catch (e) {}
    }

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({
        fuente: "google_sheets_vivos",
        datos: listadoProcesado,
      }),
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({
        error: "Fallo procesando censo",
        detalle: error.message,
      }),
    };
  }
};
